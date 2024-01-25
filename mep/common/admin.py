from dal import autocomplete
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from import_export.resources import ModelResource
from import_export.admin import ImportExportModelAdmin
from parasolr.django.signals import IndexableSignalHandler
from django.conf import settings
from django.contrib import messages
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
    max_objects_to_index = 100

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
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
            f"requesting index of {len(self.objects_to_index)} objects, dry_run = {dry_run}"
        )

        # warn if too many
        max2index = self.max_objects_to_index
        num2index = len(self.objects_to_index)
        if max2index and num2index > max2index:
            messages.warning(
                self.request,
                f"The number of updated records in need of indexing ({num2index:,})"
                f" exceeds the maximum amount indexable from the web interface ({max2index:,})."
                f" Please be aware that you will need to manually re-index this table on the server.",
            )

        # only continue if not a dry run
        if not dry_run:
            # re-enable indexing
            IndexableSignalHandler.connect()

            # index objects
            if self.objects_to_index:
                items2index = self.objects_to_index[: max2index if max2index else None]
                logger.debug(f"indexing {len(items2index):,} items now")
                self.Meta.model.index_items(items2index)
                logger.debug(f"done indexing {len(items2index):,} items")

        # turn viaf lookups back on
        settings.SKIP_VIAF_LOOKUP = False

        # make sure indexing disconnected afterward
        IndexableSignalHandler.disconnect()

    class Meta:
        skip_unchanged = True
        report_skipped = True


class ImportExportAdmin(ImportExportModelAdmin):
    resource_classes = []

    def get_export_resource_classes(self):
        """
        Specifies the resource class to use for exporting,
        so that separate fields can be exported than those imported
        """
        # Subclass this function
        return super().get_export_resource_classes()

    def get_resource_kwargs(self, request, *args, **kwargs):
        """Passing request to resource obj for use in django messages"""
        return {"request": request}


admin.site.unregister(User)
admin.site.register(User, LocalUserAdmin)
