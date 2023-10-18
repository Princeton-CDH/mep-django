


psql -d postgres -c "DROP DATABASE cdh_shxco;"
psql -d postgres -c "DROP ROLE cdh_shxco;"
psql -d postgres -c "CREATE ROLE cdh_shxco WITH CREATEDB LOGIN PASSWORD 'cdh_shxco';"
psql -d postgres -U cdh_shxco < data/13_daily_cdh_shxco_cdh_shxco_2023-04-05.Wednesday.sql


.. psql -d postgres -U shxco -c "CREATE DATABASE shxco;"

