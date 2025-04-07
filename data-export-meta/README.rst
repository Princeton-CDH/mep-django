Data exports
============

This directory contains [Frictionless data](https://frictionlessdata.io/) [data package](https://specs.frictionlessdata.io/data-package/)
files to describe and validate Project data exports, along with utility scripts for auto-generating portions of dataset readmes, data dictionaries, and list of members and books changes from previous published versions of the datasets.

Datapackage files are currently generated and maintained manually; they should be updated
for deposit with revised data exports as needed.

Validation
^^^^^^^^^^

To validate datapackage files and associated data files, use frictionless:

1. `pip install frictionless`
2. `frictionless validate vX.X/datapakage.json`

This will report any errors in the datapackage file as well as any validation errors where the types or pattern constraints specified in the data package file do not match the data in the associated CSV files.


Scripts
^^^^^^^

All scripts require pandas (`pip install pandas`).

- `readme_info.py` - use to generate dataset summary information for inclusion in plain-text readme (number of fields, number of rows, optional list of fields with descriptions); can also be used to generate a CSV data dictionary. Takes a path to the datapackage file; resource paths referenced in the datapackage must resolve.
- `member_changes.py` - for members in an old version not in the new version, creates a csv of changes with new ids for member ids that changed; requires pandas. Must be updated for new versions and should be added to changes from previous versions.
- `book_changes.py` - same as above, but for book ids