"""
This file was generated with the customdashboard management command and
contains the class for the main dashboard.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'mep-django.dashboard.CustomIndexDashboard'
"""

from django.utils.translation import ugettext_lazy as _

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard to control order.
    """

    def init_with_context(self, context):
        # site_name = get_admin_site_name(context)

        # Accounts
        self.children.append(modules.ModelList(
            _('Library Accounts'),
            column=1,
            collapsible=False,
            models=([
                'mep.accounts.models.Account',
                'mep.accounts.models.Event',
                'mep.accounts.models.Subscription',
                'mep.accounts.models.Reimbursement',
                'mep.accounts.models.SubscriptionType',
                'mep.accounts.models.Borrow',
                'mep.accounts.models.Purchase',
            ]),
        ))

        # Personography
        self.children.append(modules.ModelList(
            _('Personography'),
            column=1,
            collapsible=False,
            models=([
                'mep.people.models.Person',
                'mep.people.models.Country',
                'mep.people.models.Profession',
                'mep.people.models.RelationshipType',
                'mep.people.models.Location',
            ]),
        ))

        # Bibliography
        self.children.append(modules.ModelList(
            _('Bibliography'),
            column=1,
            collapsible=False,
            models=([
                'mep.books.models.Item',
                'mep.books.models.CreatorType',
                'mep.books.models.Format',
                'mep.books.models.Subject',
            ]),
        ))

        # Footnotes
        self.children.append(modules.ModelList(
            _('Footnotes'),
            column=1,
            collapsible=False,
            models=([
                'mep.footnotes.models.SourceType',
                'mep.footnotes.models.Bibliography',
                'mep.footnotes.models.Footnote',
            ]),
        ))

        # Administration
        self.children.append(modules.ModelList(
             _('Administration'),
            column=1,
            collapsible=False,
            models=('django.contrib.*',),
        ))

        # Recent Actions
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            collapsible=False,
            column=2,
        ))
