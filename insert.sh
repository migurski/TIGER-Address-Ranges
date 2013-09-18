#!/bin/sh -ex

cat <<CREATE

SET CLIENT_ENCODING TO UTF8;
SET STANDARD_CONFORMING_STRINGS TO ON;

SELECT DropGeometryColumn('','tiger_2013_roads','the_geom');
DROP TABLE "tiger_2013_roads";

BEGIN;

CREATE TABLE "tiger_2013_roads"
(
    gid serial PRIMARY KEY,
    "linearid" varchar(22),
    "fullname" varchar(100),
    "rttyp" varchar(1),
    "mtfcc" varchar(5)
);

SELECT AddGeometryColumn('','tiger_2013_roads','the_geom','3857','MULTILINESTRING',2);
--CREATE INDEX "tiger_2013_roads_the_geom_gist" ON "tiger_2013_roads" using gist ("the_geom" gist_geometry_ops);

COMMIT;

CREATE

for SRC in ??/tl_2013_?????_ranges.shp; do 

    FIPS=${SRC#??/tl_2013_}
    FIPS=${FIPS%_ranges.shp}
    ZIP="tl_2013_${FIPS}_roads.zip"
    URL="ftp://ftp.census.gov:21//geo/tiger/TIGER2013/ROADS/${ZIP}"
    
    curl -o $ZIP -L $URL
    unzip -quj $ZIP
    
    SHP1="${ZIP%.zip}.shp"
    SHP2="${ZIP%.zip}-merc.shp"
    
    rm -f "${ZIP%.zip}-merc.shx"
    rm -f "${ZIP%.zip}-merc.prj"
    rm -f "${ZIP%.zip}-merc.dbf"
    rm -f $SHP2
    
    ogr2ogr -t_srs EPSG:3857 $SHP2 $SHP1
    
    rm -f "${ZIP%.zip}.shx"
    rm -f "${ZIP%.zip}.prj"
    rm -f "${ZIP%.zip}.dbf"
    rm -f "${ZIP%.zip}.shp.xml"
    rm -f $SHP1 $ZIP
    
    shp2pgsql -a -s 3857 -W Windows-1252 $SHP2 tiger_2013_roads
    
    rm -f "${ZIP%.zip}-merc.shx"
    rm -f "${ZIP%.zip}-merc.prj"
    rm -f "${ZIP%.zip}-merc.dbf"
    rm -f $SHP2
    
done
