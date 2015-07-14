pytzwhere [![Build Status](https://travis-ci.org/pegler/pytzwhere.svg)](https://travis-ci.org/pegler/pytzwhere) [![Coverage Status](https://coveralls.io/repos/pegler/pytzwhere/badge.svg)](https://coveralls.io/r/pegler/pytzwhere)
=========

This is the unstable branch. Use at your own discretion.

pytzwhere is a Python library to lookup the timezone for a given lat/lng entirely offline.

It is a port from https://github.com/mattbornski/tzwhere with a few improvements. The underlying timezone data is based on work done by [Eric Muller](http://efele.net/maps/tz/world/)

If used as a library, basic usage is as follows:

    >>> from tzwhere import tzwhere
    >>> tz = tzwhere.tzwhere()
    >>> print tz.tzNameAt(35.29, -89.66)
    America/Chicago

If you have `shapely` installed, you can use that library to speed up things by a factor of hundreds. Initialization takes considerably longer (about 20 seconds longer) though. Only really makes sense if you have a lot of points to look up.
    
    >>> tz = tzwhere.tzwhere(input_kind='csv', shapely=True)
    Reading from CSV input file: tz_world.csv
    >>> print tz.tzNameAt(35.29, -89.66)
    America/Chicago

The polygons used for building the timezones are based on VMAP0. Sometimes points are outside a VMAP0 polygon, but are clearly within a certain timezone (see also this [discussion](https://github.com/mattbornski/tzwhere/issues/8)). As a somewhat 'hacky' workaround you can tell the library to return the closest timezone if it doesn't find a proper timezone. Only works if the point is reasonably close to a valid timezone in the first place. This costs you another 80MB of RAM or so. You need to use `shapely` for this. 

    >>> tz = tzwhere.tzwhere(shapely=True, forceTZ=True)
    >>> # This is on the shore of Lake Michigan
    >>> tz.tzNameAt(40.7271, -73.98)
    >>> tz.tzNameAt(40.7271, -73.98, forceTZ=True)
    'America/New_York'
    >>> tz.tzNameAt(50.1536, -5.030)
    >>> # This is slightly off the shore of Cornwall
    >>> tz.tzNameAt(50.1536, -5.030, forceTZ=True) 
    >>> 'Europe/London'
    >>> # Far off the coast of Cornwall
    >>> tz.tzNameAt(50.26, -9.051, forceTZ=True)

The module can also be run as a script, which offers some other possibilities including producing the CSV file mentioned above.  Instructions and usage information can be seen by running:

    tzwhere.py --help

Dependencies (all optional):

  * `docopt` - if you want to use `tzwhere.py` as a script (e.g. as shown above).

  * `numpy` - if you want to save about 200MB of RAM.

  * `shapely` - if you want to speed up things by a factor of hundreds
