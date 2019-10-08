from collections import OrderedDict
from functools import wraps
import re
import uuid
import pytest

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.http import Http404


def absolutize_url(local_url, request=None):
    '''Convert a local url to an absolute url, with scheme and server name,
    based on the current configured :class:`~django.contrib.sites.models.Site`.

    :param local_url: local url to be absolutized, e.g. something generated by
        :meth:`~django.core.urlresolvers.reverse`
    '''
    if local_url.startswith('https'):
        return local_url

    # add scheme and server (i.e., the http://example.com) based
    # on the django Sites infrastructure.
    root = Site.objects.get_current().domain
    # add http:// if necessary, since most sites docs
    # suggest using just the domain name
    if not root.startswith('http'):
        # if in debug mode and request is passed in, use
        # the current scheme (i.e. http for localhost/runserver)
        if settings.DEBUG and request:
            root = '%s://%s' % (request.scheme, root)
        # assume https for production sites
        else:
            root = 'https://' + root

    # make sure there is no double slash between site url and local url
    if local_url.startswith('/'):
        root = root.rstrip('/')

    return root + local_url


def alpha_pagelabels(paginator, objects, attr_meth):
    """Generate abbreviated, alphabetical page labels for pagination items.
    Label format should be something like 'Ab - Ad', 'Ard - Art'.
    :param paginator: a django paginator
    :param objects: the complete list of objects paginated by the paginator
    :param attr_meth: method or lambda to retrieve the attribute on the
        object that shoudl be used for page labels
    :returns: :class:`~collections.OrderedDict` where keys are page
        numbers and values are page labels
    """
    # adapted from Emory findingaids
    # https://github.com/emory-libraries/findingaids/blob/master/findingaids/fa/utils.py#L163

    page_labels = OrderedDict()
    labels = []

    if paginator.count <= 1:
        # if there is not enough content to paginate, bail out
        return page_labels

    # get all labels for first and last objects on each page
    for i in range(paginator.num_pages):
        page = paginator.page(i + 1)  # paginator page is 1-based
        # get objects at start & end of each page (paginator index also 1-based)
        labels.append(attr_meth(objects[page.start_index() - 1]))
        # don't go beyond the end of the actual number of objects
        end_index = min(page.end_index() - 1, paginator.count)
        # add end label only if not the same as first (e.g., page of a single item)
        if page.start_index() - 1 != end_index:
            labels.append(attr_meth(objects[end_index]))

    # abbreviate labels so they are as short as possible but distinct from
    # preceding and following labels
    abbreviated_labels = []
    # iterate over all labels and generate the shortest distinct version
    for i, label in enumerate(labels):
        next_label = labels[i + 1] if i + 1 < len(labels) else ''
        prev_label = labels[i - 1] if i > 0 else ''

        # In the rare case that two labels are *exactly* the same,
        # just add the full label.
        if label in (next_label, prev_label):
            abbreviated_labels.append(label)
            continue

        # iterate through the label one letter at a time
        # to determine the minimum length needed to differentiate
        # start with one letter, go up to full length of the label if necessary
        abbr = ''
        for j, char in enumerate(label, 1):
            abbr += char   # or abbr = label[:j]
            # if abbreviation is different from neighboring labels
            # at the current length, then use it
            if abbr not in (next_label[:j], prev_label[:j]):
                break
            # if we don't break before the loop finishes, use
            # the whole label

        abbreviated_labels.append(abbr)

    # iterate over the abbreviate labels in pairs and generate page labels
    for i in range(0, len(abbreviated_labels), 2):
        page_index = int((i + 2) / 2)
        try:
            page_labels[page_index] = '%s - %s' % \
                (abbreviated_labels[i].strip(),
                 abbreviated_labels[i + 1].strip())
        except IndexError:
            # paginator was not created with orphan protection,
            # it's possible we could get a single item at the end
            page_labels[page_index] = abbreviated_labels[i].strip()

    return page_labels


def login_temporarily_required(func):
    '''Test decorator for for views that have LoginRequiredOr404
    enabled. Creates a user with no permissions on first run for a given
    class, and logs in as that user before running the decorated test
    method. Intended for use on Django TestCase class methods.
    '''
    @wraps(func)
    def wrapper(testclass, *args, **kwargs):
        # if no login info is set, create the user
        if not hasattr(testclass, 'loginrequired_login_info'):
            # define login required user
            testclass.loginrequired_login_info = {
                'username': 'loginrequired',
                'password': str(uuid.uuid4())
            }
            User.objects.create_user(**testclass.loginrequired_login_info)

        # login with test client as the user
        testclass.client.login(**testclass.loginrequired_login_info)
        # then call the test method
        func(testclass, *args, **kwargs)
    return wrapper
