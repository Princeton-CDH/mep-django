Troubleshooting
===============

Solr setup with Docker
----------------------

Create a new docker container with the Solr 8.6 image::

    docker run --name solr86 -p 8983:8983 -t solr:8.6

Copy the solr config files in as a configset named `ppa`::

    docker cp solr_conf solr86:/opt/solr/server/solr/configsets/shxco

Change ownership  of the configset files to the `solr` user::

    docker exec --user root solr86 /bin/bash -c "chown -R solr:solr /opt/solr/server/solr/configsets/shxco"

Copy the configsets to the solr data directory::

    docker exec -d solr86 cp -r /opt/solr/server/solr/configsets /var/solr/data

Create a new core with the `ppa` configset::

    curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=shxco&configSet=shxco"

When the configset has changed, copy in the updated solr config files::

    docker cp solr_conf/* solr86:/opt/solr/server/solr/configsets/shxco/


Postgres setup
--------------

If exists, drop current::

    psql -d postgres -c "DROP DATABASE cdh_shxco;"
    psql -d postgres -c "DROP ROLE cdh_shxco;"

Create role and password::

    psql -d postgres -c "CREATE ROLE cdh_shxco WITH CREATEDB LOGIN PASSWORD 'cdh_shxco';"

Import database dump (change path as appropriate)::

    psql -d postgres -U cdh_shxco < data/13_daily_cdh_shxco_cdh_shxco_2023-12-03.Sunday.sql

Or all together to wipe database and reapply migrations::

    psql -d postgres -c "DROP DATABASE cdh_shxco;"
    psql -d postgres -c "DROP ROLE cdh_shxco;"
    psql -d postgres -c "CREATE ROLE cdh_shxco WITH CREATEDB LOGIN PASSWORD 'cdh_shxco';"
    psql -d postgres -U cdh_shxco < data/13_daily_cdh_shxco_cdh_shxco_2023-12-03.Sunday.sql
    python manage.py migrate
    python manage.py createsuperuser  # if developing locally