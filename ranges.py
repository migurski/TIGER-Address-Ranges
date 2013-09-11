from osgeo import ogr, osr
from shapely import wkb

#
# North America Albers Equal Area Conic
# http://spatialreference.org/ref/esri/102008/
#
sref_na = osr.SpatialReference()
sref_na.ImportFromProj4('+proj=aea +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs')

def features(layer):
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
    MTFCC    = names.index('MTFCC')
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
        geometry.TransformTo(sref_na)
        shape = wkb.loads(geometry.ExportToWkb())
        
        if shape.length <= 40:
            continue

        statefp  = feature.GetField(STATEFP)
        countyfp = feature.GetField(COUNTYFP)
        fullname = feature.GetField(FULLNAME)
        mtfcc    = feature.GetField(MTFCC)
        
        if feature.GetField(LFROMADD):
            
            fromadd = feature.GetField(LFROMADD)
            toadd   = feature.GetField(LTOADD)
            offset  = feature.GetField(OFFSETL)
            zip     = feature.GetField(ZIPL)
            
            yield (
                shape.parallel_offset(5., 'left'),
                statefp, countyfp, fullname, mtfcc,
                fromadd, toadd, offset, zip
                )
        
        if feature.GetField(RFROMADD):
            
            fromadd = feature.GetField(RFROMADD)
            toadd   = feature.GetField(RTOADD)
            offset  = feature.GetField(OFFSETR)
            zip     = feature.GetField(ZIPR)
            
            yield (
                shape.parallel_offset(5., 'right'),
                statefp, countyfp, fullname, mtfcc,
                fromadd, toadd, offset, zip
                )

if __name__ == '__main__':

    input_fn = 'tl_2013_06075_edges.shp'
    input_ds = ogr.Open(input_fn)
    input_lyr = input_ds.GetLayer(0)
    
    for (index, feature) in enumerate(features(input_lyr)):
        shape, statefp, countyfp, fullname, mtfcc, fromadd, toadd, offset, zip = feature
        
        print feature
        print shape
        
        if index == 16:
            break
