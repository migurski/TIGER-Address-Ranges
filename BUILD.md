GEOS Build Notes
====

I was seeing a bad crashing bug when using Shapely to do curve offsets.
The following test case will reliably segfault Shapely on an Ubuntu 12.04
server with apt-gotten GEOS:

    raw = '\x01\x02\x00\x00\x00\x06\x00\x00\x00?\xbeh\xfc\xd6\xae\x18A\x9d' \
        + '\xbeW\x99E\xa1$A\xfc\x12\xbb\xb3\x00\xaf\x18AU\x8b\xdc\xff\x1f\xa1' \
        + '$A\x03#\x82\xcd\xf2\xae\x18AAG\\R-\xa1$AU\x01\xda\x9b\xee\xae\x18A' \
        + 'Ec\xf9\xa8?\xa1$AjD\xf4=\xe5\xae\x18AI\xd6\x7f[D\xa1$A?\xbeh\xfc' \
        + '\xd6\xae\x18A\x9d\xbeW\x99E\xa1$A'
    
    from shapely import wkb
    shape = wkb.loads(raw)
    shape.parallel_offset(5., 'left')

Newer versions of GEOS appear to fix this bug, whatever the cause.

Installing Fresh GEOS
----

1. Use [virtualenv](http://www.virtualenv.org) to create a new Python package directory.
2. Download [GEOS 3.4.2](http://trac.osgeo.org/geos/), unpack and `cd` in.
3. Configure GEOS: `./configure --prefix=/path/to/virtualenv`
4. Build GEOS: `make && make install`
5. Download [Shapely](https://pypi.python.org/pypi/Shapely#downloads), unpack and `cd` in.
6. Set environment variable `LIBRARY_PATH` to */path/to/virtualenv/lib*
7. Install Shapely: `python setup.py build_ext`
8. During use, keep `LD_LIBRARY_PATH` set to */path/to/virtualenv/lib*
