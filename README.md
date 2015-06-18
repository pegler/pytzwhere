pytzwhere [![Build Status](https://travis-ci.org/pegler/pytzwhere.svg)](https://travis-ci.org/pegler/pytzwhere)
=========

pytzwhere is a Python library to lookup the timezone for a given lat/lng entirely offline

It is a port from https://github.com/mattbornski/tzwhere with a few improvements.

If used as a library, basic usage is as follows:

    >>> import tzwhere
    >>> tz = tzwhere.tzwhere()
    Reading json input file: tz_world_compact.json
    >>> print tz.tzNameAt(35.29, -89.66)
    America/Chicago

By default (and as shown above), the `tzwhere` class (at the heart of this library) initialises itself from a JSON file.  Note that this is very very memory hungry (about 750MB, though the file is much smaller).  You can save a lot of memory (hundred of megabytes) at the cost of another second or so initialisation time, by telling `tzwhere` to read its data in (one line at a time) from a CSV file instead:

    >>> tz = tzwhere.tzwhere(input_kind='csv')
    Reading from CSV input file: tz_world.csv
    >>> print tz.tzNameAt(35.29, -89.66)
    America/Chicago

The module can also be run as a script, which offers some other possibilities including producing the CSV file mentioned above.  Instructions and usage information can be seen by running:

    tzwhere.py --help

Dependencies (both optional):

  * `docopt` - if you want to use `tzwhere.py` as a script (e.g. as shown above).

  * `numpy` - if you want to save about 200MB of RAM.
