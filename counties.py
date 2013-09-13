from csv import DictReader
from urllib import urlopen
from subprocess import Popen, PIPE
from os import mkdir, chdir, getcwd, unlink
from os.path import exists
from glob import glob

def counties():
    ''' Load counties and associated state plane projection data.
    '''
    with open('state-planes.txt') as sp:
        state_planes = dict()
    
        for sp_row in DictReader(sp, dialect='excel-tab'):
            state_fips = sp_row['fips']
            plane = sp_row['plane']
            proj_code = sp_row['projection']
            proj_path = proj_code.replace(':', '/').lower()
            proj_href = 'http://spatialreference.org/ref/%s/proj4/' % proj_path
            
            key = state_fips, plane
            state_planes[key] = dict(code=proj_code, href=proj_href)
    
    with open('county-state-planes.txt') as csp:
        for csp_row in DictReader(csp, dialect='excel-tab'):
            state_fips = csp_row['fips'][0:2]
            county_fips = csp_row['fips'][2:5]
            plane = csp_row['plane']
            
            plane_key = state_fips, plane
            county = dict(projection=state_planes[plane_key])
            county.update(dict(fips=state_fips+county_fips))
            
            if state_fips != '09':
                continue
            
            if 'proj4' not in county['projection']:
                county['projection']['proj4'] \
                    = urlopen(county['projection']['href']).read().strip()
            
            yield county

if __name__ == '__main__':

    for county in counties():
    
        dir = county['fips'][:2]
        fips = county['fips']
        popd = getcwd()
    
        if not exists(dir):
            mkdir(dir)
        
        chdir(dir)
        
        out = open('%s.out' % fips, 'w')
        err = open('%s.err' % fips, 'w')
        
        try:
            zipfile = 'tl_2013_%s_edges.zip' % fips
            ziphref = 'ftp://ftp2.census.gov:21//geo/tiger/TIGER2013/EDGES/tl_2013_%s_edges.zip' % fips
            
            print 'curl', zipfile
            curl = 'curl', '-o', zipfile, '-L', ziphref
            curl = Popen(curl, stdout=out)
            curl.wait()
            
            if curl.returncode:
                raise RuntimeError()
        
            print 'unzip', zipfile
            unzip = 'unzip', '-u', zipfile
            unzip = Popen(unzip, stderr=err, stdout=out)
            unzip.wait()
            
            if unzip.returncode:
                raise RuntimeError()
            
            infile = 'tl_2013_%s_edges.shp' % fips
            outfile = 'tl_2013_%s_ranges.shp' % fips
            
            for outpart in glob('tl_2013_%s_ranges.*' % fips):
                unlink(outpart)
            
            print 'range', outfile
            ranges = 'python', '%s/ranges.py' % popd, '-p', county['projection']['proj4'], infile, outfile
            ranges = Popen(ranges, stderr=err, stdout=out)
            ranges.wait()
            
            if ranges.returncode:
                raise RuntimeError()
            
            out.close()
            err.close()
            unlink(err.name)
        
        except RuntimeError:
            for outpart in glob('tl_2013_%s_ranges.*' % fips):
                unlink(outpart)
        
        finally:
            for inpart in glob('tl_2013_%s_edges.*' % fips):
                unlink(inpart)

            chdir(popd)
