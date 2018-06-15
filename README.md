# geodjango-tzwhere

geodjango-tzwhere is a Python library to lookup the timezone for a given lat/lng entirely offline using GeoDjango and PostGIS.

This package was originally forked from https://github.com/pegler/pytzwhere, and has the same API. However, instead of loading the geojson timezone data into memory each time the app is run, this package will store it in your database during migration. Lookups will be faster, memory usage negligible, and the overhead of parsing the geojson each time your app starts is avoided.

I have tested this with PostgreSQL/PostGIS. It might work with SpatiaLite as well but I have not tested it there.

## Why should I use this instead of using pytzwhere?

Pytzwhere stores all of the timezone data in memory. This uses a lot of memory and incurs a big performance hit each time you start your app, as it has to re-parse the geojson file every time. This may be compounded in a production system where you may be running multiple instances. If you are not using a spatial database then that's really your only choice, but if you are using one, then it doesn't make sense to make these sacrifices. Use this package instead to take advantage of your database.

## Usage

If used as a library, basic usage is as follows:

    >>> from tzwhere import tzwhere
    >>> tz = tzwhere.tzwhere()
    >>> print tz.tzNameAt(35.29, -89.66)
    America/Chicago

The polygons used for building the timezones are based on VMAP0. Sometimes points are outside a VMAP0 polygon, but are clearly within a certain timezone (see also this [discussion](https://github.com/mattbornski/tzwhere/issues/8)). As a solution you can use the `forceTZ` parameter as described below.

### forceTZ

If the coordinates provided are outside of the currently defined timezone boundaries, the `tzwhere` function will return `None`. If you would like to match to the closest timezone, use the `forceTZ` parameter.

Unlike pytzwhere, the `forceTZ` parameter does not need to be provided at `tzwhere` init time. You can provide it with your call to `tzNameAt()`.

### Dependencies:

  * `django`
  * `PostGIS` or possibly some other spatial database system (at your own risk)

### Example:

    >>> from tzwhere import tzwhere
    >>> tz = tzwhere.tzwhere()
    >>> print(tz.tzNameAt(53.68193999999999, -6.239169999999998))
    None

    >>> from tzwhere import tzwhere
    >>> tz = tzwhere.tzwhere(forceTZ=True)
    >>> print(tz.tzNameAt(53.68193999999999, -6.239169999999998, forceTZ=True))
    Europe/Dublin
