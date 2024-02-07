"""
Common logic to export models.

"""

import codecs
import csv
import json
import os.path
from itertools import chain


from django.core.management.base import BaseCommand, ImproperlyConfigured
import progressbar


class ExportEncoder(json.JSONEncoder):
    """Extend :class`json.JsonEncoder`  so that generator content
    used for iterative encoding as json can be output as CSV
    at the same time.

    :param csvwriter: instance of `class:csv.DictWriter` for CSV ouptut
    :param progress: instance of `class:rich.progress.Progress` for tracking
        progress of the data used for JSON outupt
    """

    def __init__(self, csvwriter, *args, **kwargs):
        self.csvwriter = csvwriter
        super().__init__(*args, **kwargs)

    def iterencode(self, data):
        """extend iterencode to allow processing the data twice"""
        # wrap the generator in a new stream array,
        # so that we can process it before handoff for json encoding
        # don't display progress for the second stream array
        restream = StreamArray(self.reprocess_data(data), data.total, progress=False)
        return super().iterencode(restream)

    def reprocess_data(self, data):
        """Generator: output each item in the data as CSV, then yield"""
        for element in data:
            # export to csv
            self.csvwriter.writerow(BaseExport.flatten_dict(element))
            yield element


class BaseExport(BaseCommand):
    """
    Export model data in CSV and JSON formats. Takes an optional argument to
    specify the output directory. Otherwise, files are created in the current
    directory.

    Children must set `model` to define the model being exported, and define
    :meth:`get_object_data()` to transform a single model instance into a dict
    that will be used for export.

    To control the subset of exported models, children can override and filter
    :meth:`get_queryset`.
    """

    #: specify a model here or override get_queryset() for more control
    model = None

    #: fields for CSV output, should be list of str
    csv_fields = None

    def add_arguments(self, parser):
        parser.add_argument(
            "-d",
            "--directory",
            help="Specify the directory where files should be generated",
        )
        parser.add_argument(
            "-m",
            "--max",
            type=int,
            help="Maximum number of objects to export (for testing)",
        )

    def handle(self, *args, **kwargs):
        """Export all model data into a CSV file and JSON file."""
        # check that CSV export fields are defined before running
        if self.csv_fields is None:
            raise ImproperlyConfigured(
                "%(cls)s has no fields defined for CSV export. Define the "
                "csv_fields list property." % {"cls": self.__class__.__name__}
            )

        # define the output file
        base_filename = self.get_base_filename()
        if kwargs["directory"]:
            base_filename = os.path.join(kwargs["directory"], base_filename)

        # get stream array / generator of data for export
        data = self.get_data(kwargs.get("max"))
        self.stdout.write("Exporting JSON and CSV")
        # ensure directory exists (useful to allow command line user to specify dated dir)
        os.makedirs(os.path.dirname(base_filename), exist_ok=True)
        # open and initialize CSV file
        with open("{}.csv".format(base_filename), "w") as csvfile:
            # write utf-8 byte order mark at the beginning of the file
            csvfile.write(codecs.BOM_UTF8.decode())
            csvwriter = csv.DictWriter(csvfile, fieldnames=self.csv_fields)
            csvwriter.writeheader()

            # iteratively export as CSV and JSON
            with open("{}.json".format(base_filename), "w") as jsonfile:
                exporter = ExportEncoder(indent=2, csvwriter=csvwriter)
                for chunk in exporter.iterencode(data):
                    jsonfile.write(chunk)

    def get_base_filename(self):
        """
        Base filename to use for export. Uses model's plural verbose name
        by default, .e.g "events.json" and "events.csv". Returns the filename
        without an extension.
        """
        if self.model is None:
            raise ImproperlyConfigured(
                "%(cls)s is missing a model. Set the model property to a django"
                "Model class." % {"cls": self.__class__.__name__}
            )
        # force evaluation of proxy; otherwise os.path.join() will error
        return str(self.model._meta.verbose_name_plural)

    def get_queryset(self):
        """
        Return the list of items for this export. The return value must be an
        iterable and may be a QuerySet.
        """
        if self.model is not None:
            queryset = self.model._default_manager.all()
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, or override %(cls)s.get_queryset()."
                % {"cls": self.__class__.__name__}
            )

        return queryset

    def get_data(self, maximum=None):
        """
        Convert all models into an intermediary object form suitable for
        transforming into export formats.
        """
        objects = self.get_queryset()
        # grab the first N if maximum is specified
        if maximum:
            objects = objects[:maximum]
        total = objects.count()
        return StreamArray((self.get_object_data(obj) for obj in objects), total)

    def get_object_data(self, obj):
        """
        Convert a single model into a dict that is suitable for transforming
        into export formats (JSON, CSV).
        """
        raise NotImplementedError

    @staticmethod
    def flatten_dict(data):
        """
        Flatten a dictionary with nested dictionaries or lists into a
        key value pairs that can be output as CSV.  Nested dictionaries will be
        flattened and keys combined; lists will be converted into semi-colon
        delimited strings.
        """
        flat_data = {}
        for key, val in data.items():
            # for a nested subdictionary, combine key and nested key
            if isinstance(val, dict):
                # recurse to handle lists in nested dicts
                for subkey, subval in BaseExport.flatten_dict(val).items():
                    flat_data["_".join([key, subkey])] = subval
            # convert list to a delimited string
            elif isinstance(val, list):
                # check for list of dict
                if val and isinstance(val[0], dict):
                    # get a list of all keys present in any of the dictionaries
                    subkeys = set(chain.from_iterable(i.keys() for i in val))
                    # flatten each field into a list of values
                    for subkey in subkeys:
                        flat_data["_".join([key, subkey])] = ";".join(
                            [str(v.get(subkey, "")) for v in val]
                        )

                # otherwise, assume list of values (e.g., string or integer)
                else:
                    # convert to string before joining (e.g., list of integer)
                    flat_data[key] = ";".join([str(v) for v in val])
            else:
                flat_data[key] = val

        return flat_data


class StreamArray(list):
    """
    Wrapper for a generator so data can be streamed and encoded as json.
    Includes progressbar output that updates as the generator is consumed.

    :param gen: generator with data to be exported
    :param total: total number of items in the generator, for
        initializing the progress bar
    """

    # adapted from answer on
    # https://stackoverflow.com/questions/21663800/python-make-a-list-generator-json-serializable

    def __init__(self, gen, total, progress=True):
        self.show_progress = progress
        if self.show_progress:
            self.progbar = progressbar.ProgressBar(
                redirect_stdout=True, max_value=total
            )
            self.progress = 0
        self.gen = gen
        self.total = total

    def __iter__(self):
        for element in self.gen:
            # update progress bar if progress is being shown
            if self.show_progress:
                self.progress += 1
                self.progbar.update(self.progress)
            yield element

        if self.show_progress:
            # mark progress bar as finished when iteration finishes
            self.progbar.finish()

    def __len__(self):
        return self.total
