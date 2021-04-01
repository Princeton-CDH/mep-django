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
members_v1 = 'https://dataspace.princeton.edu/bitstream/88435/dsp0105741v63x/7/SCoData_members_v1_2020-07.csv'
# local copy of v1.1
members_v1_1 = 'SCoData_members_v1.1_2021-01.csv'

if __name__ == '__main__':
    members_v1_df = pd.read_csv(members_v1)
    members_df = pd.read_csv(members_v1_1)

    # identify members in v1.1 not in v1.0
    # FIXME: not useful because of merge/rename
    new_members = members_df[~members_df.uri.isin(members_v1_df.uri)]
    print('%d new members in 1.1 not included in 1.0' % len(new_members))
    new_uris = list(new_members.uri)

    # identify members from v1 with uri not included in v1.1
    removed_members = members_v1_df[~members_v1_df.uri.isin(members_df.uri)]
    print('%d members from 1.0 no longer included in 1.1' % len(removed_members))

    with open('SCoData_members_removed.csv', 'w') as csvfile:
        fieldnames = ['uri', 'new_uri', 'status', 'in_version', 'removed_version']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        defaults = {'in_version': '1.0', 'removed_version': '1.1'}
        for member in removed_members.itertuples():
            response = requests.get(member.uri, allow_redirects=False)
            info = defaults.copy()
            info['uri'] = member.uri
            if response.status_code == 301:
                new_uri = response.headers.get('Location')
                info['new_uri'] = new_uri
                # if the uri is in the new member uris, mark as renamed
                if new_uri in new_uris:
                    info['status'] = 'renamed'
                # otherwise mark as merged
                else:
                    info['status'] = 'merged'
            elif response.status_code == 404:
                info['status'] = 'deleted'
            else:
                print('Unexpected status code %s for %s' %
                      (response.status_code, member.uri))

            writer.writerow(info)

    # identify new members that are not renames
    removed_df = pd.read_csv('SCoData_members_removed.csv')
    new_members = new_members[~new_members.uri.isin(removed_df.new_uri)]
    print(new_members)

