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


# published v1 members dataset
members_v1 = "https://dataspace.princeton.edu/bitstream/88435/dsp0105741v63x/7/SCoData_members_v1_2020-07.csv"
# local copy of v1.1
# members_v1_1 = 'SCoData_members_v1.1_2021-01.csv'
# local copy of v1.2 (not yet published)
members_v1_2 = "SCoData_members_v1.2_2022-01.csv"

if __name__ == "__main__":
    old_version = "1.1"
    new_version = "1.2"
    members_v1_df = pd.read_csv(members_v1)
    # members_v1_1_df = pd.read_csv(members_v1_1)
    members_df = pd.read_csv(members_v1_2)

    # identify members in new version not in the previous
    # FIXME: not useful because of merge/rename
    new_members = members_df[~members_df.uri.isin(members_v1_df.uri)]
    print(
        "%d new members in %s not included in %s"
        % (len(new_members, old_version, new_version))
    )
    new_uris = list(new_members.uri)

    # identify members from previous version with uri not included in newer version
    removed_members = members_v1_df[~members_v1_df.uri.isin(members_df.uri)]
    print(
        "%d members from %s no longer included in %s"
        % (len(removed_members), old_version, new_version)
    ),

    with open("SCoData_members_removed.csv", "a") as csvfile:
        fieldnames = ["uri", "new_uri", "status", "in_version", "removed_version"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # don't write header since we're appending now
        # writer.writeheader()
        defaults = {"in_version": old_version, "removed_version": new_version}
        for member in removed_members.itertuples():
            response = requests.get(member.uri, allow_redirects=False)
            info = defaults.copy()
            info["uri"] = member.uri
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
                    % (response.status_code, member.uri)
                )

            writer.writerow(info)

    # identify new members that are not renames
    removed_df = pd.read_csv("SCoData_members_removed.csv")
    new_members = new_members[~new_members.uri.isin(removed_df.new_uri)]
    print(new_members)
