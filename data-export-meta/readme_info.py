#!/usr/bin/env python

# utility script to generate readme information based on CSV and datapackage
#
# pip install pandas
# usage:
#   python readme_info.py datapackage

import json
import sys
import argparse
import pathlib

import pandas as pd


def readme_info(df, dp_resource, field_list=True):
    print("1. Number of fields: %d\n" % len(df.columns))
    print("2. Number of rows: {:,}\n".format(len(df)))
    schema_fields = dp_resource["schema"]["fields"]

    assert len(schema_fields) == len(df.columns)
    field_info = {field["name"]: field for field in schema_fields}

    if field_list:
        print("3. Field List:")
        for col in df.columns:
            print("%s : %s" % (col, field_info[col]["description"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Generate dataset info readme from datapackage and data files"
    )
    parser.add_argument("datapackage", type=pathlib.Path)
    # flag to determine whether fields be listed
    parser.add_argument(
        "--field-list",
        help="Generate field list in readme.txt format",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    args = parser.parse_args()

    with args.datapackage.open() as packagejson:
        datapackage = json.load(packagejson)

        for resource in datapackage["resources"]:
            # resource path should be relative to the datapackage file
            datafile = args.datapackage.parent / resource["path"]
            print("\n\nInspecting %s...\n\n" % datafile)
            with datafile.open() as csvfile:
                df = pd.read_csv(csvfile)
            readme_info(df, resource, field_list=args.field_list)
