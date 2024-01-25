from dal import autocomplete
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from import_export.resources import ModelResource
from parasolr.django.signals import IndexableSignalHandler
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class NamedNotableAdmin(admin.ModelAdmin):
    """Generic model admin for named/notable models."""

    list_display = ("name", "note_snippet")
    # fields = ('name', 'notes')
    search_fields = ("name", "notes")


class CollapsibleTabularInline(admin.TabularInline):
    """Django admin tabular inline with grappelli collapsible classes added"""

    classes = ("grp-collapse grp-open",)


class CollapsedTabularInline(admin.TabularInline):
    """
    Django admin tabular inline with grappelli collapsible classes added,
    defaulting to collapsed.
    """

    classes = ("grp-collapse grp-closed",)


class LocalUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + (
        "is_superuser",
        "is_active",
        "last_login",
        "group_names",
    )

    def group_names(self, obj):
        """custom property to display group membership"""
        if obj.groups.exists():
            return ", ".join(g.name for g in obj.groups.all())

    group_names.short_description = "groups"


class ImportExportModelResource(ModelResource):
    def __init__(self, *x, **y):
        super().__init__(*x, **y)
        # list to contain updated objects for batch indexing at end
        self.objects_to_index = []

    def before_import(self, dataset, *args, **kwargs):
        # lower and camel_case headers
        dataset.headers = [x.lower().replace(" ", "_") for x in dataset.headers]

        # turn off indexing temporarily
        IndexableSignalHandler.disconnect()

        # turn off viaf lookups
        settings.SKIP_VIAF_LOOKUP = True

    def before_import_row(self, row, **kwargs):
        """
        Called on an OrderedDictionary of row attributes.
        Opportunity to do quick string formatting as a
        principle of charity to annotators before passing
        values into django-import-export lookup logic.
        """
        pass

    def after_save_instance(self, instance, using_transactions, dry_run):
        """
        Called when an instance either was or would be saved (depending on dry_run)
        """
        self.objects_to_index.append(instance)
        return super().after_save_instance(instance, using_transactions, dry_run)

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        """
        Called after importing, twice: once with dry_run==True (preview),
        once dry_run==False. We report how many objects were updated and need to be indexed.
        We only do so when dry_run is False.
        """
        # run parent method
        super().after_import(dataset, result, using_transactions, dry_run, **kwargs)

        # report how many need indexing
        logger.debug(
            f"indexing {len(self.objects_to_index)} objects, dry_run = {dry_run}"
        )

        # only continue if not a dry run
        if not dry_run:
            # re-enable indexing
            IndexableSignalHandler.connect()

            # index objects
            if self.objects_to_index:
                self.Meta.model.index_items(self.objects_to_index)

        # turn viaf lookups back on
        settings.SKIP_VIAF_LOOKUP = False

        # make sure indexing disconnected afterward
        IndexableSignalHandler.disconnect()

    class Meta:
        skip_unchanged = True
        report_skipped = True


admin.site.unregister(User)
admin.site.register(User, LocalUserAdmin)
