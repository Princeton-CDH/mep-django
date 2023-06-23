import time
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse
from parasolr.query.queryset import EmptySolrQuerySet
import pytest

from mep.books.models import PastWorkSlug, Work
from mep.books.views import WorkCirculation, WorkCardList, WorkList
from mep.common.utils import absolutize_url, login_temporarily_required
from mep.footnotes.models import Footnote


class BooksViews(TestCase):
    fixtures = ["sample_works"]

    def setUp(self):
        self.admin_pass = "password"
        self.admin_user = get_user_model().objects.create_superuser(
            "admin", "admin@example.com", self.admin_pass
        )

    def test_work_autocomplete(self):
        # remove fixture items to duplicate previous test conditions
        Work.objects.all().delete()

        url = reverse("books:work-autocomplete")
        res = self.client.get(url)

        # getting the view returns 200
        assert res.status_code == 200
        data = res.json()
        # there is a results list in the JSON
        assert "results" in data
        # it is empty because there are no accounts or query
        assert not data["results"]

        # - test basic search and sort

        # search by title
        work1 = Work.objects.create(
            title="Poems Two Painters", mep_id="mep:01", notes="Author: Knud Merrild"
        )
        work2 = Work.objects.create(title="Collected Poems", mep_id="mep:02")
        res = self.client.get(url, {"q": "poems"})
        data = res.json()
        assert res.status_code == 200
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["results"][0]["text"] == work2.title
        assert data["results"][1]["text"] == work1.title

        # search by note text
        res = self.client.get(url, {"q": "knud"})
        data = res.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["text"] == work1.title

        # search by mep id
        res = self.client.get(url, {"q": "mep:02"})
        data = res.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["text"] == work2.title


class TestWorkListView(TestCase):
    fixtures = ["sample_works", "multi_creator_work"]

    def setUp(self):
        # index fixtures and give time for index to take effect
        Work.index_items(Work.objects.all())
        time.sleep(10)
        # bind some convenience items
        self.factory = RequestFactory()
        self.url = reverse("books:books-list")

    def test_list(self):
        response = self.client.get(self.url)

        # should display all works in the database
        works = Work.objects.all()
        assert response.context["works"].count() == works.count()
        for work in works:
            self.assertContains(response, work.title)
            self.assertContains(response, work.year)
            self.assertContains(
                response, reverse("books:book-detail", args=[work.slug])
            )
            self.assertContains(response, work.get_absolute_url())
            self.assertContains(response, work.work_format)

        # item with UNCERTAINTYICON in notes should show text to SRs
        self.assertContains(response, Work.UNCERTAINTY_MESSAGE)

        # NOTE publishers display is designed but data not yet available

    @patch("mep.common.views.SolrQuerySet")
    def test_last_modified(self, mock_wsq):
        mock_wsq.return_value.filter.return_value.order_by.return_value.only.return_value = [
            {"last_modified": "2018-07-02T21:08:46.428Z"}
        ]
        response = self.client.head(self.url)
        # has last modified header
        assert response["Last-Modified"]

    def test_no_relevance_anonymous(self):
        response = self.client.get(self.url, {"query": "eliza"})
        # relevance score should not be shown to anynmous user
        self.assertNotContains(
            response,
            '<dt class="relevance">Relevance</dt>',
            msg_prefix="relevance score not displayed for anonymous users",
        )

    @login_temporarily_required
    def test_relevance_logged_in(self):
        response = self.client.get(self.url, {"query": "eliza"})
        # relevance score should be shown to logged-in users
        self.assertContains(
            response,
            '<dt class="relevance">Relevance</dt>',
            msg_prefix="relevance score displayed for logged in users",
        )

    def test_form(self):
        response = self.client.get(self.url)
        # filter form should be displayed with filled-in query field one time
        self.assertContains(response, "Search by title, author, or keyword", count=1)
        # should show total result count
        self.assertContains(response, "%d total results" % Work.objects.count())

    def test_form_no_result(self):
        # no results - display error text & image
        response = self.client.get(self.url, {"query": "foobar"})
        self.assertContains(response, "No search results found")
        # empty search - no image
        self.assertNotContains(response, "img/no-results-error-1x.png")

    @patch.dict(WorkList.solr_sort, {"title": "undefined"})
    def test_form_errors(self):
        # force solr error by sending garbage sort value
        response = self.client.get(self.url)
        self.assertContains(response, "Something went wrong.")
        # error - show image
        self.assertContains(response, "img/no-results-error-1x.png")

    def test_many_authors(self):
        response = self.client.get(self.url)

        # multi-author item should show first three authors
        novelists = Work.objects.get(pk=4126)
        self.assertContains(response, novelists.authors[0])
        self.assertContains(response, novelists.authors[1])
        self.assertContains(response, novelists.authors[2])

        # other authors should be hidden
        self.assertNotContains(response, novelists.authors[3])

        # should show "...x more authors" text
        self.assertContains(response, "...15 more authors")

    def test_get_queryset(self):
        # create a mocked form
        view = WorkList()
        form = Mock()
        view.get_form = Mock(return_value=form)
        view.request = self.factory.get(self.url)
        # if form is valid, should return all works sorted by chosen sort
        form.is_valid.return_value = True
        form.cleaned_data = {"sort": "title", "circulation_dates": ""}
        solr_qs = view.get_queryset()
        db_qs = Work.objects.order_by("sort_title")
        # querysets from solr and db should match
        for index, item in enumerate(solr_qs):
            assert db_qs[index].title == item["title"][0]
            assert db_qs[index].slug == item["slug"]
        # if form is invalid, should return empty queryset
        form.is_valid.return_value = False
        solr_qs = view.get_queryset()
        assert isinstance(solr_qs, EmptySolrQuerySet)

        # circulation dates set
        form.cleaned_data = {"sort": "title", "circulation_dates": (1935, None)}
        form.is_valid.return_value = True
        solr_qs = view.get_queryset()
        db_qs = Work.objects.filter(event__start_date__year__gt=1935)
        # currently only one record in the db with an event (1936)
        assert solr_qs.count() == db_qs.count()
        assert db_qs[0].slug == solr_qs[0]["slug"]

        form.cleaned_data = {"sort": "title", "circulation_dates": (1919, 1922)}
        solr_qs = view.get_queryset()
        assert solr_qs.count() == 0

    def test_get_page_labels(self):
        # create a mocked form and some fake works to paginate
        view = WorkList()
        form = Mock()
        view.get_form = Mock(return_value=form)
        view.request = self.factory.get(self.url)
        works = range(120)
        paginator = Paginator(works, per_page=view.paginate_by)
        # if form is valid, should use default implementation (numbered pages)
        # NOTE this will change if we implement alpha pagination for this view
        form.is_valid.return_value = True
        form.cleaned_data = {"sort": "relevance"}
        page_labels = view.get_page_labels(paginator)
        assert page_labels == [(1, "1 – 100"), (2, "101 – 120")]
        # if invalid, should return one page with 'N/A' label
        form.is_valid.return_value = False
        page_labels = view.get_page_labels(paginator)
        assert page_labels == [(1, "N/A")]

        # alpha page labels depending on sort
        form.is_valid.return_value = True
        view.queryset = Mock()
        page_label_results = [
            {"sort_title_isort": "ABC books"},
            {"sort_title_isort": "Charlie Day"},
        ]
        view.queryset.only.return_value.get_results.return_value = page_label_results
        form.cleaned_data = {"sort": "title"}
        paginator = Paginator(page_label_results, per_page=view.paginate_by)
        page_labels = view.get_page_labels(paginator)
        # assert page_labels == [(1, 'ABC – Char')]
        # only one entry; couldn't get odict items comparison to work otherwise
        for i, val in page_labels:
            assert i == 1
            assert val == "ABC – Char"
        view.queryset.only.assert_called_with(view.solr_sort["title"])
        view.queryset.only.return_value.get_results.assert_called_with(rows=100000)

    def test_pagination(self):
        response = self.client.get(self.url)
        # pagination options set in context
        assert response.context["page_labels"]
        # current fixture is not enough to paginate
        # next/prev links should have aria-hidden to indicate not usable
        self.assertContains(response, '<a rel="prev" aria-hidden')
        self.assertContains(response, '<a rel="next" aria-hidden')
        # pagination labels are used, current page selected
        self.assertContains(
            response,
            '<option value="1" selected="selected">%s</option>'
            % list(response.context["page_labels"])[0][1],
        )

    @patch("mep.books.views.WorkSolrQuerySet")
    def test_get_range_stats(self, mock_wsq):
        # NOTE: This depends on configuration for mapping the fields
        # in the range_field_map class attribute of MembersList
        mock_stats = {"stats_fields": {"event_years": {"min": 1919.0, "max": 1962.0}}}
        mock_wsq.return_value.stats.return_value.get_stats.return_value = mock_stats
        range_minmax = WorkList().get_range_stats()
        # returns integer years
        # also converts membership_dates to
        assert range_minmax == {"circulation_dates": (1919, 1962)}
        # call for the correct field in stats
        args, kwargs = mock_wsq.return_value.stats.call_args_list[0]
        assert "event_years" in args
        # if get stats returns None, should return an empty dict
        mock_wsq.return_value.stats.return_value.get_stats.return_value = None
        assert WorkList().get_range_stats() == {}
        # None set for min or max should result in the field not being
        # returned (but the other should be passed through as expected)
        mock_wsq.return_value.stats.return_value.get_stats.return_value = mock_stats
        mock_stats["stats_fields"]["event_years"]["min"] = None
        assert WorkList().get_range_stats() == {}


class TestWorkDetailView(TestCase):
    fixtures = ["sample_works", "multi_creator_work"]

    @patch("mep.common.views.SolrQuerySet")
    def test_last_modified(self, mock_wsq):
        mock_wsq.return_value.filter.return_value.order_by.return_value.only.return_value = [
            {"last_modified": "2018-07-02T21:08:46.428Z"}
        ]
        work = Work.objects.first()
        url = reverse("books:book-detail", kwargs={"slug": work.slug})
        response = self.client.head(url)
        # has last modified header
        assert response["Last-Modified"]
        mock_wsq.return_value.filter.assert_called_with(
            item_type="work", slug_s=work.slug
        )
        mock_wsq.return_value.filter.return_value.order_by.assert_called_with(
            "-last_modified"
        )
        mock_wsq.return_value.filter.return_value.order_by.return_value.only.assert_called_with(
            "last_modified"
        )

    def test_get_breadcrumbs(self):
        # fetch any work and check breadcrumbs
        work = Work.objects.first()
        url = reverse("books:book-detail", kwargs={"slug": work.slug})
        response = self.client.get(url)
        breadcrumbs = response.context["breadcrumbs"]
        # last crumb should be the title of the work
        self.assertEqual(breadcrumbs[-1][0], work.title)
        # second to last crumb should be the work list
        self.assertEqual(breadcrumbs[-2][0], WorkList.page_title)

    def test_creators_display(self):
        # fetch a multi-creator work
        work = Work.objects.get(pk=4126)
        url = reverse("books:book-detail", kwargs={"slug": work.slug})
        response = self.client.get(url)
        # all authors should be listed as <dd> elements under <dt>
        self.assertContains(response, '<dt class="creator">Author</dt>')
        for author in work.authors:
            self.assertContains(response, '<dd class="creator">%s</dd>' % author.name)
        # editors should be listed as <dd> elements under <dt>
        self.assertContains(response, '<dt class="creator">Editor</dt>')
        for editor in work.editors:
            self.assertContains(response, '<dd class="creator">%s</dd>' % editor.name)

    def test_pubdate_display(self):
        # fetch a work with a publication date
        work = Work.objects.get(pk=1)
        url = reverse("books:book-detail", kwargs={"slug": work.slug})
        response = self.client.get(url)
        # check that the publication date is a <dd> under a <dt>
        self.assertContains(response, '<dt class="pubdate">Publication Date</dt>')
        self.assertContains(response, '<dd class="pubdate">%s</dd>' % work.year)

    def test_format_display(self):
        # fetch some works with different formats
        book = Work.objects.get(title="Murder on the Blue Train")
        periodical = Work.objects.get(title="The Dial")
        # check the rendering of the format indicator
        url = reverse("books:book-detail", kwargs={"slug": book.slug})
        response = self.client.get(url)
        self.assertContains(response, '<dd class="format">Book</dd>')
        url = reverse("books:book-detail", kwargs={"slug": periodical.slug})
        response = self.client.get(url)
        self.assertContains(response, '<dd class="format">Periodical</dd>')

    def test_read_link_display(self):
        # fetch a work with an ebook url
        work = Work.objects.get(title="The Dial")
        url = reverse("books:book-detail", kwargs={"slug": work.slug})
        response = self.client.get(url)
        # check that a link was rendered
        self.assertContains(
            response,
            '<a href="%s" target="_blank">Read online</a>' % work.ebook_url,
            html=True,
        )

    def test_notes_display(self):
        # fetch a work with public notes
        work = Work.objects.get(title="Chronicle of my Life")
        url = reverse("books:book-detail", kwargs={"slug": work.slug})
        response = self.client.get(url)
        # check that the notes are rendered as a <dd> under a <dt>
        self.assertContains(response, "<dt>Notes</dt>")
        self.assertContains(response, "<dd>%s</dd>" % work.public_notes)
        # NOTE check that uncertainty icon is rendered when implemented

    def test_markdown_notes(self):
        work = Work.objects.get(title="Chronicle of my Life")
        work.public_notes = "some *formatted* content"
        work.save()
        url = reverse("books:book-detail", kwargs={"slug": work.slug})
        response = self.client.get(url)
        # check that markdown is rendered
        self.assertContains(response, "<em>formatted</em>")


class TestWorkCirculation(TestCase):
    fixtures = ["test_events"]

    def setUp(self):
        self.work = Work.objects.get(title="The Dial")
        self.view = WorkCirculation()
        self.view.kwargs = {"slug": self.work.slug}

    def test_get_queryset(self):
        # make sure that works only get events associated with them
        events = self.view.get_queryset()
        for event in events:
            assert event.work == self.work

    def test_get_context_data(self):
        # ensure work and page title are stored in context
        self.view.object_list = self.view.get_queryset()
        context = self.view.get_context_data()
        assert context["work"] == self.work
        assert context["page_title"] == "The Dial Circulation Activity"

    def test_get_breadcrumbs(self):
        # breadcrumbs order should be: home, works list, work detail, work circ.
        self.view.object_list = self.view.get_queryset()
        self.view.get_context_data()
        crumbs = self.view.get_breadcrumbs()
        assert crumbs[0][0] == "Home"
        assert crumbs[1][0] == "Books"
        assert crumbs[2][0] == "The Dial"
        assert crumbs[3][0] == "Circulation"

    def test_template(self):
        response = self.client.get(
            reverse("books:book-circ", kwargs={"slug": self.work.slug})
        )
        # table headers
        self.assertContains(response, "Member")
        self.assertContains(response, "Start Date")
        self.assertContains(response, "End Date")
        self.assertContains(response, "Status")
        self.assertContains(response, "Volume/Issue")
        # name & link to member who borrowed book
        self.assertContains(response, "L. Michaelides")
        self.assertContains(response, "/members/michaelides-l")
        # start/end date of borrow
        self.assertContains(response, "Oct 21, 1920")
        self.assertContains(response, "Oct 25, 1920")
        # status
        self.assertContains(response, "Borrow")
        # issue info
        self.assertContains(response, "Vol. 69, no. 4, October 1920")

    def test_no_events(self):
        # work with no events should show message instead of table
        work = Work.objects.create(title="fake book")
        response = self.client.get(
            reverse("books:book-circ", kwargs={"slug": work.slug})
        )
        self.assertNotContains(response, "<table")
        self.assertContains(response, "No documented circulation activity")


class TestWorkCardList(TestCase):
    fixtures = ["test_events"]

    def setUp(self):
        self.work = Work.objects.get(slug="lonigan-young-manhood")
        self.view = WorkCardList()
        self.view.kwargs = {"slug": self.work.slug}

    def test_get_queryset(self):
        queryset = self.view.get_queryset()
        # retrieves and stores work
        assert self.view.work == self.work
        work_borrow = self.work.event_set.first().borrow
        work_footnotes = work_borrow.event_ptr.footnotes.all()

        # finds footnotes for this work with images and de-dupes based on image
        assert list(queryset) == list(work_footnotes)

        # ignores footnote with no image
        fn1 = work_footnotes.first()
        # Create footnote on the same event object but with no image
        fn_noimage = Footnote.objects.create(
            bibliography=fn1.bibliography,
            content_type=fn1.content_type,
            object_id=fn1.object_id,
        )
        # create second footnote on the same image
        fn2 = Footnote.objects.create(
            bibliography=fn1.bibliography,
            content_type=fn1.content_type,
            object_id=fn1.object_id,
            image=fn1.image,
        )

        card_footnotes = list(self.view.get_queryset())
        assert fn_noimage not in card_footnotes
        assert fn2 in card_footnotes
        assert fn1 in card_footnotes

    def test_get_queryset_notfound(self):
        view = WorkCardList()
        view.kwargs = {"slug": "bogus"}
        with pytest.raises(Http404):
            view.get_queryset()

    def test_get_absolute_url(self):
        """Full URI for work card list page."""
        assert self.view.get_absolute_url() == absolutize_url(
            reverse("books:book-card-list", args=[self.work.slug])
        )

    def test_get_breadcrumbs(self):
        self.view.work = self.work  # normally set by get_queryset
        crumbs = self.view.get_breadcrumbs()
        assert crumbs[-1][0] == "Cards"
        assert crumbs[-1][1] == self.view.get_absolute_url()
        assert crumbs[2][0] == self.work.title
        assert crumbs[2][1] == absolutize_url(self.work.get_absolute_url())

    def test_get_breadcrumbs_display(self):
        # confirm that breadcrumbs are rendered by the template
        url = reverse("books:book-card-list", kwargs={"slug": self.work.slug})
        response = self.client.get(url)
        self.assertContains(response, '<nav class="breadcrumbs">')
        self.assertContains(response, self.view.get_absolute_url())
        self.assertContains(response, self.work.title)

    def test_get_context_data(self):
        self.view.object_list = self.view.get_queryset()
        context = self.view.get_context_data()
        assert context["work"] == self.work
        assert context["footnotes"] == self.view.object_list

    def test_template(self):
        url = reverse("books:book-card-list", kwargs={"slug": self.work.slug})
        response = self.client.get(url)

        work_borrow = self.work.event_set.first().borrow
        work_footnote = work_borrow.event_ptr.footnotes.first()
        # image included in two sizes
        self.assertContains(response, work_footnote.image.image.size(width=225))
        self.assertContains(response, work_footnote.image.image.size(width=450))
        # member name
        member = work_borrow.account.persons.first()
        self.assertContains(response, member.sort_name)
        # event date
        self.assertContains(response, work_borrow.start_date.strftime("%b %d, %Y"))
        # link to card detail view with event id
        self.assertContains(
            response,
            "%s#e%d"
            % (
                reverse(
                    "people:member-card-detail",
                    args=[member.slug, work_footnote.image.short_id],
                ),
                work_borrow.pk,
            ),
        )


class TestPastSlugRedirects(TestCase):
    fixtures = ["sample_works"]

    # short id for first canvas in manifest for stein's card
    canvas_id = "68fd36f1-a463-441e-9f13-dfc4a6cd4114"
    kwargs = {"slug": "stein-gertrude", "short_id": canvas_id}

    def setUp(self):
        self.work = Work.objects.get(slug="dial")
        self.slug = self.work.slug
        self.old_slug = "old_slug"
        PastWorkSlug.objects.create(work=self.work, slug=self.old_slug)

    def test_work_detail_pages(self):
        # single member detail pages that don't require extra args
        for named_url in ["book-detail", "book-circ", "book-card-list"]:
            # old slug should return permanent redirect to equivalent new
            route = "books:%s" % named_url
            response = self.client.get(reverse(route, kwargs={"slug": self.old_slug}))

            assert response.status_code == 301  # permanent redirect
            # redirect to same view with the *correct* slug
            assert response["location"].endswith(
                reverse(route, kwargs={"slug": self.slug})
            )

            # check that it still 404s correctly
            response = self.client.get(reverse(route, kwargs={"slug": "foo"}))
            assert response.status_code == 404
