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
import time

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
    max_objects_to_index = 1000
    use_transactions = False
    # store updated objects for bulk indexing after import completes
    store_instance = True

    def __init__(self, *args, **kwargs):
        # NOTE: request is not passed in by default;
        # extend get_resource_kwargs or use LocalImportExportModelAdmin
        self.request = kwargs.get("request", None)
        super().__init__(*args, **kwargs)

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        # lower and snake_case headers
        dataset.headers = [x.lower().replace(" ", "_") for x in dataset.headers]

        # log summary of what will be done
        logger.debug(
            f"importing dataset with {len(dataset.headers)} columns "
            + f"(using_transactions={using_transactions}, dry_run={dry_run})"
        )

        # turn off indexing temporarily
        IndexableSignalHandler.disconnect()

        # turn off viaf lookups
        settings.SKIP_VIAF_LOOKUP = True

    def validate_row_by_slug(self, row):
        """Make sure the record to update can be found by slug or past slug; if the slug is a past slug, row data is updated to use the current slug."""
        if not row.get("slug"):
            return False
        if not self.Meta.model.objects.filter(slug=row["slug"]).exists():
            # past slug?
            instance = self.Meta.model.objects.filter(
                past_slugs__slug=row["slug"]
            ).first()
            if instance:
                logger.debug(
                    f'Record found by past slug {row["slug"]}, updating to {instance.slug}'
                )
                row["slug"] = instance.slug
            else:
                err = f'{self.Meta.model.__name__} with slug {row["slug"]} not found'
                logger.error(err)
                return False
        return True

    def skip_row(self, instance, original, row, import_validation_errors=None):
        if not self.validate_row_by_slug(row):
            return True
        return super().skip_row(instance, original, row, import_validation_errors)

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        """
        After import completes, report how many objects were updated and
        need to be indexed. When `dry_run` is true, this is called to display
        import preview; indexing is only done when `dry_run` is false.
        """
        # default implementation does nothing, no need to call parent method
        # result is a list of rowresult obects; we only care
        # about updates since we don't support creation or deletion
        updated_objects = [
            row_result.instance
            for row_result in result
            if row_result.import_type == "update"
        ]

        # if this is a dry run, report how many would be indexd
        if dry_run:
            # report how many need indexing
            logger.debug(f"{len(updated_objects):,} records to index")

        # is this is not a dry run, index the updated objects
        else:
            if updated_objects:
                # get objects to index, up to configured maximum
                items2index = updated_objects[: self.max_objects_to_index]

                # do the actual indexing
                start = time.time()
                self.Meta.model.index_items(items2index)
                logger.debug(
                    f"Indexing {len(items2index):,} records in {time.time() - start:.1f} seconds"
                )
                # warn if there are updated records that were not indexud
                n_indexed, n_updated = len(items2index), len(updated_objects)
                n_remaining = n_updated - n_indexed
                if n_remaining:
                    msg = (
                        f"Updated {n_updated:,} records and indexed the first {n_indexed:,}. "
                        f"The remaining {n_remaining:,} must be indexed on the server."
                    )
                    logger.debug(msg)
                    messages.warning(self.request, msg)

        # turn viaf lookups back on
        settings.SKIP_VIAF_LOOKUP = False

        # re-enable indexing
        IndexableSignalHandler.connect()

    # FIXME: no longer needed?
    def ensure_nulls(self, row):
        for k, v in row.items():
            row[k] = v if v or v == 0 else None

    class Meta:
        skip_unchanged = True
        report_skipped = True


class LocalImportExportModelAdmin(ImportExportModelAdmin):
    resource_classes = []

    # def get_export_resource_classes(self):
    #     """
    #     Specifies the resource class to use for exporting,
    #     so that separate fields can be exported than those imported
    #     """
    #     # Subclass this function
    #     return super().get_export_resource_classes()

    def get_resource_kwargs(self, request, *args, **kwargs):
        """Pass request object to resource for use in django messages"""
        kwargs = super().get_resource_kwargs(request, *args, **kwargs)
        # pass request object in so we can use messages to warn
        kwargs["request"] = request
        return kwargs


admin.site.unregister(User)
admin.site.register(User, LocalUserAdmin)
