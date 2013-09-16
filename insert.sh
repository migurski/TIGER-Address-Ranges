#!/bin/sh -ex

for SRC in ??/tl_2013_?????_ranges.shp; do 

    FIPS=${SRC#??/tl_2013_}
    FIPS=${FIPS%_ranges.shp}
    ZIP="tl_2013_${FIPS}_edges.zip"
    URL="ftp://ftp.census.gov:21//geo/tiger/TIGER2013/EDGES/${ZIP}"
    
    curl -o $ZIP -L $URL
    unzip -quj $ZIP
    
    SHP="${ZIP%.zip}.shp"
    
    shp2pgsql -a -n -W Windows-1252 $SHP tiger_2013_edgeinfo
    
    rm -f "${ZIP%.zip}.shx"
    rm -f "${ZIP%.zip}.prj"
    rm -f "${ZIP%.zip}.dbf"
    rm -f "${ZIP%.zip}.shp.xml"
    rm -f $ZIP $SHP
    
done
