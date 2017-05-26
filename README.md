pytzwhere [![Build Status](https://travis-ci.org/pegler/pytzwhere.svg)](https://travis-ci.org/pegler/pytzwhere) [![Coverage Status](https://coveralls.io/repos/pegler/pytzwhere/badge.svg)](https://coveralls.io/r/pegler/pytzwhere)
=========

pytzwhere is a Python library to lookup the timezone for a given lat/lng entirely offline. 

Version 3.0 fixes how `pytzwhere` deals with [holes](https://github.com/pegler/pytzwhere/issues/34) in timezones. It is recommended that you use version 3.0.

It is a port from https://github.com/mattbornski/tzwhere with a few improvements. The underlying timezone data is based on work done by [Eric Muller](http://efele.net/maps/tz/world/)

If used as a library, basic usage is as follows:

    >>> from tzwhere import tzwhere
    >>> tz = tzwhere.tzwhere()
    >>> print tz.tzNameAt(35.29, -89.66)
    America/Chicago

The polygons used for building the timezones are based on VMAP0. Sometimes points are outside a VMAP0 polygon, but are clearly within a certain timezone (see also this [discussion](https://github.com/mattbornski/tzwhere/issues/8)). As a solution you can search for the closest timezone within a user defined radius.



Dependencies:

  * `numpy` (optional)

  * `shapely`
