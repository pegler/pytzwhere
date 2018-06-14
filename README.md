geodjango-tzwhere
=========

geodjango-tzwhere is a Python library to lookup the timezone for a given lat/lng entirely offline using GeoDjango and PostGIS.

This package was originally forked from https://github.com/pegler/pytzwhere, and has the same API. However, instead of loading the geojson timezone data into memory each time the app is run, this package will store it in your database during migration. Lookups should be faster, and the overhead of parsing the geojson each time is avoided.

I have tested this with PostgreSQL/PostGIS. It probably will work with SpatiaLite as well but I have not tested it there.

If used as a library, basic usage is as follows:

    >>> from tzwhere import tzwhere
    >>> tz = tzwhere.tzwhere()
    >>> print tz.tzNameAt(35.29, -89.66)
    America/Chicago

The polygons used for building the timezones are based on VMAP0. Sometimes points are outside a VMAP0 polygon, but are clearly within a certain timezone (see also this [discussion](https://github.com/mattbornski/tzwhere/issues/8)). As a solution you can search for the closest timezone within a user defined radius.



Dependencies:

  * `django`

  * `PostGIS` or possibly some other spatial database system (at your own risk)



**forceTZ**

If the coordinates provided are outside of the currently defined timezone boundaries, the `tzwhere` function will return `None`. If you would like to match to the closest timezone, use the `forceTZ` parameter.

Unlike pytzwhere, the `forceTZ` parameter does not need to be provided at `tzwhere` init time. You can provide it with your call to `tzNameAt()`.

Example:

    >>> from tzwhere import tzwhere
    >>> tz = tzwhere.tzwhere()
    >>> print(tz.tzNameAt(53.68193999999999, -6.239169999999998))
    None

    >>> from tzwhere import tzwhere
    >>> tz = tzwhere.tzwhere(forceTZ=True)
    >>> print(tz.tzNameAt(53.68193999999999, -6.239169999999998, forceTZ=True))
    Europe/Dublin

