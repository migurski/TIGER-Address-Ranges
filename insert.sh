#!/bin/sh -ex

for SHP in ??/*_ranges.shp; do 

    shp2pgsql -a -s 3857 -W Windows-1252 $SHP tiger_2013_ranges

done
