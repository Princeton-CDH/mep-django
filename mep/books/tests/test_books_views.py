import time
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.test import RequestFactory, TestCase
from django.urls import reverse

from mep.books.models import Edition, Work
from mep.books.views import WorkList
from mep.common.utils import login_temporarily_required


class BooksViews(TestCase):
    fixtures = ['sample_works']

    def setUp(self):
        self.admin_pass = 'password'
        self.admin_user = get_user_model().objects.create_superuser(
            'admin', 'admin@example.com', self.admin_pass)

    def test_work_autocomplete(self):
        # remove fixture items to duplicate previous test conditions
        Work.objects.all().delete()

        url = reverse('books:work-autocomplete')
        res = self.client.get(url)

        # getting the view returns 200
        assert res.status_code == 200
        data = res.json()
        # there is a results list in the JSON
        assert 'results' in data
        # it is empty because there are no accounts or query
        assert not data['results']

        # - test basic search and sort

        # search by title
        work1 = Work.objects.create(title='Poems Two Painters', mep_id='mep:01',
                                    notes='Author: Knud Merrild')
        work2 = Work.objects.create(title='Collected Poems', mep_id='mep:02')
        res = self.client.get(url, {'q': 'poems'})
        data = res.json()
        assert res.status_code == 200
        assert 'results' in data
        assert len(data['results']) == 2
        assert data['results'][0]['text'] == work2.title
        assert data['results'][1]['text'] == work1.title

        # search by note text
        res = self.client.get(url, {'q': 'knud'})
        data = res.json()
        assert len(data['results']) == 1
        assert data['results'][0]['text'] == work1.title

        # search by mep id
        res = self.client.get(url, {'q': 'mep:02'})
        data = res.json()
        assert len(data['results']) == 1
        assert data['results'][0]['text'] == work2.title


class TestWorkListView(TestCase):
    fixtures = ['sample_works', 'multi_creator_work']

    def setUp(self):
        # index fixtures and give time for index to take effect
        Work.index_items(Work.objects.all())
        time.sleep(10)
        # bind some convenience items
        self.factory = RequestFactory()
        self.url = reverse('books:books-list')

    def test_login_required_or_404(self):
        # 404 if not logged in; TEMPORARY
        assert self.client.get(self.url).status_code == 404

    @login_temporarily_required
    def test_list(self):
        response = self.client.get(self.url)

        # should display all works in the database
        works = Work.objects.all()
        assert response.context['works'].count() == works.count()
        for work in works:
            self.assertContains(response, work.title)
            self.assertContains(response, work.year)
            self.assertContains(response,
                                reverse('books:book-detail', args=[work.slug]))
            self.assertContains(response, work.get_absolute_url())
            self.assertContains(response, work.work_format)

        # item with UNCERTAINTYICON in notes should show text to SRs
        self.assertContains(response, Work.UNCERTAINTY_MESSAGE)

        # NOTE publishers display is designed but data not yet available

    @login_temporarily_required
    def test_relevance(self):
        response = self.client.get(self.url, {'query': 'eliza'})
        # relevance score should be shown to logged-in users
        self.assertContains(
            response, '<dt class="relevance">Relevance</dt>',
            msg_prefix='relevance score displayed for logged in users')

    @login_temporarily_required
    def test_form(self):
        response = self.client.get(self.url)
        # filter form should be displayed with filled-in query field one time
        self.assertContains(response, 'Search book', count=1)
        # should show total result count
        self.assertContains(response, '%d total results' % Work.objects.count())

    @login_temporarily_required
    def test_form_no_result(self):
        # no results - display error text & image
        response = self.client.get(self.url, {'query': 'foobar'})
        self.assertContains(response, 'No search results found')
        # empty search - no image
        self.assertNotContains(response, 'img/no-results-error-1x.png')

    @login_temporarily_required
    @patch.dict(WorkList.solr_sort, {'title': 'undefined'})
    def test_form_errors(self):
        # force solr error by sending garbage sort value
        response = self.client.get(self.url)
        self.assertContains(response, 'Something went wrong.')
        # error - show image
        self.assertContains(response, 'img/no-results-error-1x.png')

    @login_temporarily_required
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
        self.assertContains(response, '...15 more authors')

    def test_get_queryset(self):
        # create a mocked form
        view = WorkList()
        form = Mock()
        view.get_form = Mock(return_value=form)
        view.request = self.factory.get(self.url)
        # if form is valid, should return all works sorted by chosen sort
        form.is_valid.return_value = True
        form.cleaned_data = {'sort': 'title', 'circulation_dates': ''}
        solr_qs = view.get_queryset()
        db_qs = Work.objects.order_by('sort_title')
        # querysets from solr and db should match
        for index, item in enumerate(solr_qs):
            assert db_qs[index].title == item['title'][0]
            assert db_qs[index].slug == item['slug']
        # if form is invalid, should return empty queryset
        form.is_valid.return_value = False
        solr_qs = view.get_queryset()
        # NOTE replace with EmptySolrQueryset check when implemented in parasolr
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
        form.cleaned_data = {'sort': 'relevance'}
        page_labels = view.get_page_labels(paginator)
        assert page_labels == [(1, '1 – 100'), (2, '101 – 120')]
        # if invalid, should return one page with 'N/A' label
        form.is_valid.return_value = False
        page_labels = view.get_page_labels(paginator)
        assert page_labels == [(1, 'N/A')]

        # alpha page labels depending on sort
        form.is_valid.return_value = True
        view.queryset = Mock()
        page_label_results = [
            {'sort_title_isort': 'ABC books'},
            {'sort_title_isort': 'Charlie Day'},
        ]
        view.queryset.only.return_value.get_results \
            .return_value = page_label_results
        form.cleaned_data = {'sort': 'title'}
        paginator = Paginator(page_label_results, per_page=view.paginate_by)
        page_labels = view.get_page_labels(paginator)
        # assert page_labels == [(1, 'ABC – Char')]
        # only one entry; couldn't get odict items comparison to work otherwise
        for i, val in page_labels:
            assert i == 1
            assert val == 'ABC – Char'
        view.queryset.only.assert_called_with(view.solr_sort['title'])
        view.queryset.only.return_value.get_results \
            .assert_called_with(rows=100000)

    @login_temporarily_required
    def test_pagination(self):
        response = self.client.get(self.url)
        # pagination options set in context
        assert response.context['page_labels']
        # current fixture is not enough to paginate
        # next/prev links should have aria-hidden to indicate not usable
        self.assertContains(response, '<a rel="prev" aria-hidden')
        self.assertContains(response, '<a rel="next" aria-hidden')
        # pagination labels are used, current page selected
        self.assertContains(
            response,
            '<option value="1" selected="selected">%s</option>' %
            list(response.context['page_labels'])[0][1])


class TestWorkDetailView(TestCase):
    fixtures = ['sample_works', 'multi_creator_work']

    def test_login_required_or_404(self):
        # 404 if not logged in; TEMPORARY
        work = Work.objects.first()
        url = reverse('books:book-detail', kwargs={'slug': work.slug})
        assert self.client.get(url).status_code == 404

    @login_temporarily_required
    def test_get_breadcrumbs(self):
        # fetch any work and check breadcrumbs
        work = Work.objects.first()
        url = reverse('books:book-detail', kwargs={'slug': work.slug})
        response = self.client.get(url)
        breadcrumbs = response.context['breadcrumbs']
        # last crumb should be the title of the work
        self.assertEqual(breadcrumbs[-1][0], work.title)
        # second to last crumb should be the work list
        self.assertEqual(breadcrumbs[-2][0], WorkList.page_title)

    @login_temporarily_required
    def test_creators_display(self):
        # fetch a multi-creator work
        work = Work.objects.get(pk=4126)
        url = reverse('books:book-detail', kwargs={'slug': work.slug})
        response = self.client.get(url)
        # all authors should be listed as <dd> elements under <dt>
        self.assertContains(response, '<dt class="creator">Author</dt>')
        for author in work.authors:
            self.assertContains(response, '<dd class="creator">%s</dd>' % author.name)
        # editors should be listed as <dd> elements under <dt>
        self.assertContains(response, '<dt class="creator">Editor</dt>')
        for editor in work.editors:
            self.assertContains(response, '<dd class="creator">%s</dd>' % editor.name)

    @login_temporarily_required
    def test_pubdate_display(self):
        # fetch a work with a publication date
        work = Work.objects.get(pk=1)
        url = reverse('books:book-detail', kwargs={'slug': work.slug})
        response = self.client.get(url)
        # check that the publication date is a <dd> under a <dt>
        self.assertContains(response, '<dt class="pubdate">Publication Date</dt>')
        self.assertContains(response, '<dd class="pubdate">%s</dd>' % work.year)

    @login_temporarily_required
    def test_format_display(self):
        # fetch some works with different formats
        book = Work.objects.get(title='Murder on the Blue Train')
        periodical = Work.objects.get(title='The Dial')
        # check the rendering of the format indicator
        url = reverse('books:book-detail', kwargs={'slug': book.slug})
        response = self.client.get(url)
        self.assertContains(response, '<dd class="format">Book</dd>')
        url = reverse('books:book-detail', kwargs={'slug': periodical.slug})
        response = self.client.get(url)
        self.assertContains(response, '<dd class="format">Periodical</dd>')

    @login_temporarily_required
    def test_read_link_display(self):
        # fetch a work with an ebook url
        work = Work.objects.get(title='The Dial')
        url = reverse('books:book-detail', kwargs={'slug': work.slug})
        response = self.client.get(url)
        # check that a link was rendered
        self.assertContains(response,
            '<a href="%s">Read online</a>' % work.ebook_url)

    @login_temporarily_required
    def test_notes_display(self):
        # fetch a work with public notes
        work = Work.objects.get(title='Chronicle of my Life')
        url = reverse('books:book-detail', kwargs={'slug': work.slug})
        response = self.client.get(url)
        # check that the notes are rendered as a <dd> under a <dt>
        self.assertContains(response, '<dt>Notes</dt>')
        self.assertContains(response, '<dd>%s</dd>' % work.public_notes)
        # NOTE check that uncertainty icon is rendered when implemented

    @login_temporarily_required
    def test_edition_volume_display(self):
        # fetch a periodical with issue information
        work = Work.objects.get(title='The Dial')
        issues = Edition.objects.filter(work=work)
        url = reverse('books:book-detail', kwargs={'slug': work.slug})
        response = self.client.get(url)
        # check that all issues are rendered in a list format
        self.assertContains(response, '<h2>Volume/Issue</h2>')
        for issue in issues:
            self.assertContains(response, issue.display_html())
