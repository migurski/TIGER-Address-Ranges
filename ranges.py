from optparse import OptionParser

from osgeo import ogr, osr
from shapely.geometry import LineString, Point
from shapely import wkb

def features(layer, sref_local):
    ''' Generate a stream of left and right offset streets.
    
        See also `CREATE TABLE tiger_2012_edges_102008` from
        https://gist.github.com/migurski/6096576
    '''
    feature = layer.GetFeature(0)
    fields = feature.GetFieldCount()
    names = [feature.GetFieldDefnRef(i).name for i in range(fields)]
    
    STATEFP  = names.index('STATEFP')
    COUNTYFP = names.index('COUNTYFP')
    ROADFLG  = names.index('ROADFLG')
    TLID     = names.index('TLID')
    FULLNAME = names.index('FULLNAME')

    OFFSETL  = names.index('OFFSETL')
    LFROMADD = names.index('LFROMADD')
    LTOADD   = names.index('LTOADD')
    ZIPL     = names.index('ZIPL')

    OFFSETR  = names.index('OFFSETR')
    RFROMADD = names.index('RFROMADD')
    RTOADD   = names.index('RTOADD')
    ZIPR     = names.index('ZIPR')
    
    for feature in layer:
        if feature.GetField(ROADFLG) != 'Y':
            continue
        
        geometry = feature.GetGeometryRef()
        geometry.TransformTo(sref_local)
        shape = wkb.loads(geometry.ExportToWkb())
        
        if shape.length <= 40:
            continue

        statefp  = feature.GetField(STATEFP)
        countyfp = feature.GetField(COUNTYFP)
        fullname = feature.GetField(FULLNAME)
        tlid     = feature.GetField(TLID)
        
        if feature.GetField(LFROMADD):
            
            fromadd = feature.GetField(LFROMADD)
            toadd   = feature.GetField(LTOADD)
            offset  = feature.GetField(OFFSETL)
            zip     = feature.GetField(ZIPL)
            
            shape_left = shape.parallel_offset(5., 'left')
            geoms = getattr(shape_left, 'geoms', [shape_left])
            
            for geom in geoms:
                yield (
                    LineString(geom),
                    statefp, countyfp, fullname, tlid,
                    fromadd, toadd, offset, zip
                    )
        
        if feature.GetField(RFROMADD):
            
            fromadd = feature.GetField(RFROMADD)
            toadd   = feature.GetField(RTOADD)
            offset  = feature.GetField(OFFSETR)
            zip     = feature.GetField(ZIPR)
            
            shape_right = shape.parallel_offset(5., 'right')
            geoms = getattr(shape_right, 'geoms', [shape_right])
            
            for geom in geoms:
                # When offsetting to the right, coordinates come back reversed.
                yield (
                    LineString(list(reversed(geom.coords))),
                    statefp, countyfp, fullname, tlid,
                    fromadd, toadd, offset, zip
                    )

def define_fields(source_layer, dest_layer):
    ''' Define fields on a destination layer based on source layer.
    '''
    source_defn = source_layer.GetLayerDefn()
    fields = source_defn.GetFieldCount()
    names = [source_defn.GetFieldDefn(i).name for i in range(fields)]
    
    mapping = (
        ('STATEFP', 'STATEFP'),
        ('COUNTYFP', 'COUNTYFP'),
        ('FULLNAME', 'FULLNAME'),
        ('TLID', 'TLID'),
        ('LFROMADD', 'FROMADD'),
        ('LTOADD', 'TOADD'),
        ('OFFSETL', 'OFFSET'),
        ('ZIPL', 'ZIP'),
        )
    
    for (source_name, dest_name) in mapping:
    
        index = names.index(source_name)
        type = source_defn.GetFieldDefn(index).type
        width = source_defn.GetFieldDefn(index).width

        field_defn = ogr.FieldDefn(dest_name, type)
        field_defn.SetWidth(width)

        dest_layer.CreateField(field_defn)

def truncate(line, distance):
    ''' Cut a line at both ends, if it's long enough.
    
        Borrowed from cut(), defined in Shapely docs:
        http://toblerity.org/shapely/manual.html#object.project
    '''
    if distance <= 0. or line.length <= distance * 2:
        return LineString(line)
    
    #
    # Cut off the head.
    #
    coords = list(line.coords)
    
    for (i, p) in enumerate(coords):
        pd = line.project(Point(p))
        
        if pd == distance:
            # cut line here
            _line = LineString(coords[i:])
            break
        
        if pd > distance:
            # cut line before this point
            cp = line.interpolate(distance)
            _line = LineString([(cp.x, cp.y)] + coords[i:])
            break
    
    #
    # Cut off the tail.
    #
    _coords = list(_line.coords)
    _distance = _line.length - distance
    
    for (i, p) in reversed(list(enumerate(_coords))):
        pd = _line.project(Point(p))
        
        if pd == _distance:
            # cut line here
            return LineString(_coords[:i+1])
        
        if pd < _distance:
            # cut line before this point
            cp = _line.interpolate(_distance)
            return LineString(_coords[:i+1] + [(cp.x, cp.y)])

#
# North America Albers Equal Area Conic
# http://spatialreference.org/ref/esri/102008/
#
defaults = dict(proj4='+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs')

parser = OptionParser(usage='%prog [options] <input file> <output file>')

parser.set_defaults(**defaults)

parser.add_option('-p', '--proj4', dest='proj4',
                  help='Proj.4 string to use as local projection, default "%(proj4)s"' % defaults)

if __name__ == '__main__':

    options, (input_fn, output_fn) = parser.parse_args()

    # This. Is. Python.
    ogr.UseExceptions()
    
    #
    # Prepare projections.
    #
    sref_loc = osr.SpatialReference()
    sref_loc.ImportFromProj4(options.proj4)

    # Web Spherical Mercator
    # http://spatialreference.org/ref/sr-org/6864/
    sref_sm = osr.SpatialReference()
    sref_sm.ImportFromProj4('+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=6378137 +b=6378137 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs')
    
    xform_loc2sm = osr.CoordinateTransformation(sref_loc, sref_sm)
    
    #
    # Open files.
    #
    input_ds = ogr.Open(input_fn)
    input_lyr = input_ds.GetLayer(0)
    input_gt = input_lyr.GetLayerDefn().GetGeomType()
    
    if input_gt != ogr.wkbLineString:
        raise ValueError('Wrong geometry type in %s: %d' % (input_fn, input_gt))
    
    output_dr = ogr.GetDriverByName('ESRI Shapefile')
    output_ds = output_dr.CreateDataSource(output_fn)
    output_lyr = output_ds.CreateLayer('', sref_sm, ogr.wkbLineString)
    
    define_fields(input_lyr, output_lyr)
    
    for (index, details) in enumerate(features(input_lyr, sref_loc)):
        shape, statefp, countyfp, fullname, tlid, fromadd, toadd, offset, zip = details

        print statefp, countyfp, fullname
        
        feature = ogr.Feature(output_lyr.GetLayerDefn())

        feature.SetField('STATEFP', statefp)
        feature.SetField('COUNTYFP', countyfp)
        feature.SetField('FULLNAME', fullname)
        feature.SetField('TLID', tlid)
        feature.SetField('FROMADD', fromadd)
        feature.SetField('TOADD', toadd)
        feature.SetField('OFFSET', offset)
        feature.SetField('ZIP', zip)
        
        truncated_shape = truncate(shape, 15)
        geometry = ogr.CreateGeometryFromWkb(wkb.dumps(truncated_shape))
        geometry.Transform(xform_loc2sm)
        feature.SetGeometry(geometry)
        
        output_lyr.CreateFeature(feature)
