#!/usr/bin/env python

# utility script to generate a csv with information on members removed
# from previous versions of the members dataset
#
# pip install pandas
# usage:
#   python member_changes.py

import csv

import pandas as pd

import requests


# published v1.1 books dataset
books_previous = "https://dataspace.princeton.edu/bitstream/88435/dsp016d570067j/2/SCoData_books_v1.1_2021-01.csv"
# local copy of v1.2 (not yet published)
books_new = "SCoData_books_v1.2_2022-01.csv"

if __name__ == "__main__":
    old_version = "1.1"
    new_version = "1.2"
    books_prev_df = pd.read_csv(books_previous)
    # members_v1_1_df = pd.read_csv(members_v1_1)
    books_df = pd.read_csv(books_new)

    # identify members in new version not in the previous
    # FIXME: probably not useful because of merge/rename
    new_books = books_df[~books_df.uri.isin(books_prev_df.uri)]
    print("%d new books in %s not included in %s" % (len(new_books), old_version, new_version))
    new_uris = list(new_books.uri)

    # identify boks from previous version with uri not included in newer version
    removed_books = books_prev_df[~books_prev_df.uri.isin(books_df.uri)]
    print(
        "%d books from %s no longer included in %s"
        % (len(removed_books), old_version, new_version)
    ),

    with open("SCoData_books_removed.csv", "a") as csvfile:
        fieldnames = ["uri", "new_uri", "status", "in_version", "removed_version"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # don't write header if appending
        writer.writeheader()
        defaults = {"in_version": old_version, "removed_version": new_version}
        for book in removed_books.itertuples():
            response = requests.get(book.uri, allow_redirects=False)
            info = defaults.copy()
            info["uri"] = book.uri
            if response.status_code == 301:
                new_uri = response.headers.get("Location")
                info["new_uri"] = new_uri
                # if the uri is in the new member uris, mark as renamed
                if new_uri in new_uris:
                    info["status"] = "renamed"
                # otherwise mark as merged
                else:
                    info["status"] = "merged"
            elif response.status_code == 404:
                info["status"] = "deleted"
            else:
                print(
                    "Unexpected status code %s for %s"
                    % (response.status_code, book.uri)
                )

            writer.writerow(info)

    # identify new members that are not renames
    removed_df = pd.read_csv("SCoData_books_removed.csv")
    new_books = new_books[~new_books.uri.isin(removed_df.new_uri)]
    print(new_books)
