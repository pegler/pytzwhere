#!/usr/bin/env python

"""tzwhere.py - time zone computation from latitude/longitude.

Ordinarily this is loaded as a module and instances of the tzwhere
class are instantiated and queried directly, but the module can be run
as a script too (this requires the docopt package to be installed).
Run it with the -h option to see usage.

"""

import csv
import datetime
try:
    import json
except ImportError:
    import simplejson as json
import math
import os
import pickle

# We can save about 222MB of RAM by turning our polygon lists into
# numpy arrays rather than tuples, if numpy is installed.
try:
    import numpy
    WRAP = numpy.array
except ImportError:
    WRAP = tuple


class tzwhere(object):

    SHORTCUT_DEGREES_LATITUDE = 1
    SHORTCUT_DEGREES_LONGITUDE = 1
    # By default, use the data file in our package directory
    DEFAULT_JSON = os.path.join(os.path.dirname(__file__),
        'tz_world_compact.json')
    DEFAULT_PICKLE = os.path.join(os.path.dirname(__file__),
        'tz_world.pickle')
    DEFAULT_CSV = os.path.join(os.path.dirname(__file__),
        'tz_world.csv')

    def __init__(self, input_kind='json', path=None):

        # Construct appropriate generator for (tz, polygon) pairs.
        if input_kind in ['json', 'pickle']:
            featureCollection = tzwhere.read_tzworld(input_kind, path)
            pgen = tzwhere._feature_collection_polygons(featureCollection)
        elif input_kind == 'csv':
            pgen = tzwhere._read_polygons_from_csv(path)
        else:
            raise ValueError(input_kind)

        # Turn that into an internal mapping.
        self._construct_polygon_map(pgen)

        # Construct lookup shortcuts.
        self._construct_shortcuts()

    def _construct_polygon_map(self, polygon_generator):
        """Turn a (tz, polygon) generator, into our internal mapping."""
        self.timezoneNamesToPolygons = {}
        for (tzname, raw_poly) in polygon_generator:
            if tzname not in self.timezoneNamesToPolygons:
                self.timezoneNamesToPolygons[tzname] = []
            self.timezoneNamesToPolygons[tzname].append(
                WRAP(tzwhere._raw_poly_to_poly(raw_poly)))

        # Convert polygon lists to numpy arrays or (failing that)
        # tuples to save memory.
        for tzname in self.timezoneNamesToPolygons.keys():
            self.timezoneNamesToPolygons[tzname] = \
                WRAP(self.timezoneNamesToPolygons[tzname])

    def _construct_shortcuts(self):

        self.timezoneLongitudeShortcuts = {}
        self.timezoneLatitudeShortcuts = {}
        for tzname in self.timezoneNamesToPolygons:
            for polyIndex, poly in enumerate(self.timezoneNamesToPolygons[tzname]):
                lats = [x[0] for x in poly]
                lngs = [x[1] for x in poly]
                minLng = (math.floor(min(lngs) / self.SHORTCUT_DEGREES_LONGITUDE)
                          * self.SHORTCUT_DEGREES_LONGITUDE)
                maxLng = (math.floor(max(lngs) / self.SHORTCUT_DEGREES_LONGITUDE)
                          * self.SHORTCUT_DEGREES_LONGITUDE)
                minLat = (math.floor(min(lats) / self.SHORTCUT_DEGREES_LATITUDE)
                          * self.SHORTCUT_DEGREES_LATITUDE)
                maxLat = (math.floor(max(lats) / self.SHORTCUT_DEGREES_LATITUDE)
                          * self.SHORTCUT_DEGREES_LATITUDE)
                degree = minLng
                while degree <= maxLng:
                    if degree not in self.timezoneLongitudeShortcuts:
                        self.timezoneLongitudeShortcuts[degree] = {}

                    if tzname not in self.timezoneLongitudeShortcuts[degree]:
                        self.timezoneLongitudeShortcuts[degree][tzname] = []

                    self.timezoneLongitudeShortcuts[degree][tzname].append(polyIndex)
                    degree = degree + self.SHORTCUT_DEGREES_LONGITUDE

                degree = minLat
                while degree <= maxLat:
                    if degree not in self.timezoneLatitudeShortcuts:
                        self.timezoneLatitudeShortcuts[degree] = {}

                    if tzname not in self.timezoneLatitudeShortcuts[degree]:
                        self.timezoneLatitudeShortcuts[degree][tzname] = []

                    self.timezoneLatitudeShortcuts[degree][tzname].append(polyIndex)
                    degree = degree + self.SHORTCUT_DEGREES_LATITUDE

        # Convert things to tuples to save memory
        for degree in self.timezoneLatitudeShortcuts:
            for tzname in self.timezoneLatitudeShortcuts[degree].keys():
                self.timezoneLatitudeShortcuts[degree][tzname] = \
                    tuple(self.timezoneLatitudeShortcuts[degree][tzname])
        for degree in self.timezoneLongitudeShortcuts.keys():
            for tzname in self.timezoneLongitudeShortcuts[degree].keys():
                self.timezoneLongitudeShortcuts[degree][tzname] = \
                    tuple(self.timezoneLongitudeShortcuts[degree][tzname])

    def _point_inside_polygon(self, x, y, poly):
        n = len(poly)
        inside = False

        p1x, p1y = poly[0][1], poly[0][0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n][1], poly[i % n][0]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def tzNameAt(self, latitude, longitude):
        latTzOptions = self.timezoneLatitudeShortcuts[
            (math.floor(latitude / self.SHORTCUT_DEGREES_LATITUDE)
             * self.SHORTCUT_DEGREES_LATITUDE)
        ]
        latSet = set(latTzOptions.keys())
        lngTzOptions = self.timezoneLongitudeShortcuts[
            (math.floor(longitude / self.SHORTCUT_DEGREES_LONGITUDE)
             * self.SHORTCUT_DEGREES_LONGITUDE)
        ]
        lngSet = set(lngTzOptions.keys())
        possibleTimezones = lngSet.intersection(latSet)
        if possibleTimezones:
            if False and len(possibleTimezones) == 1:
                return possibleTimezones.pop()
            else:
                for tzname in possibleTimezones:
                    polyIndices = set(latTzOptions[tzname]).intersection(set(lngTzOptions[tzname]))
                    for polyIndex in polyIndices:
                        poly = self.timezoneNamesToPolygons[tzname][polyIndex]
                        if self._point_inside_polygon(longitude, latitude, poly):
                            return tzname

    @staticmethod
    def read_tzworld(input_kind='json', path=None):
        reader = tzwhere.read_json if input_kind == 'json' else tzwhere.read_pickle
        return reader(path)

    @staticmethod
    def read_json(path=None):
        if path is None:
            path = tzwhere.DEFAULT_JSON
        print('Reading json input file: %s' % path)
        with open(path, 'r') as f:
            featureCollection = json.load(f)
        return featureCollection

    @staticmethod
    def read_pickle(path=None):
        if path is None:
            path = tzwhere.DEFAULT_PICKLE
        print('Reading pickle input file: %s' % path)
        with open(path, 'r') as f:
            featureCollection = pickle.load(f)
        return featureCollection

    @staticmethod
    def write_pickle(featureCollection, path=DEFAULT_PICKLE):
        print 'Writing pickle output file: %s' % path
        with open(path, 'wb') as f:
            pickle.dump(featureCollection, f, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def _read_polygons_from_csv(path=None):
        if path is None:
            path = tzwhere.DEFAULT_CSV
        print('Reading from CSV input file: %s' % path)
        with open(path, 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                yield(row[0], [float(x) for x in row[1:]])

    @staticmethod
    def write_csv(featureCollection, path=DEFAULT_CSV):
        print 'Writing csv output file: %s' % path
        with open(path, 'w') as f:
            writer = csv.writer(f)
            for (tzname, polygon) in tzwhere._feature_collection_polygons(
                    featureCollection):
                writer.writerow([tzname] + polygon)

    @staticmethod
    def _feature_collection_polygons(featureCollection):
        """Turn a feature collection into an iterator over polygons.

        Given a featureCollection of the kind loaded from the json
        input, unpack it to an iterator which produces a series of
        (tzname, polygon) pairs, one for every polygon in the
        featureCollection.  Here tzname is a string and polygon is a
        list of floats.

        """
        for feature in featureCollection['features']:
            tzname = feature['properties']['TZID']
            if feature['geometry']['type'] == 'Polygon':
                polys = feature['geometry']['coordinates']
                for poly in polys:
                    yield (tzname, poly)

    @staticmethod
    def _raw_poly_to_poly(raw_poly):
        # WPS84 coordinates are [long, lat], while many conventions
        # are [lat, long]. Our data is in WPS84. Convert to an
        # explicit format which geolib likes.
        assert len(raw_poly) % 2 == 0
        poly = []
        while raw_poly:
            lat = raw_poly.pop()
            lng = raw_poly.pop()
            poly.append((lat, lng))
        return poly


HELP = """tzwhere.py - time zone computation from latitude/longitude.

Usage:
  tzwhere.py [options] test [<input_path>]
  tzwhere.py [options] write_pickle [<input_path>] [<output_path>]
  tzwhere.py [options] write_csv [<input_path>] [<output_path>]

Modes:

  test - run unit tests on some test locations, where we simply test that
         the computed timezone for a given location is the one we expect.
         <input_path> is the path to read in, and defaults to an
         appropriate value depending on the --kind option as follows:

             json...: {default_json}
             pickle.: {default_pickle}
             csv....: {default_csv}

  write_pickle - write out a pickle file of a feature collection;
                 <input_path> is as with test.  <output_path> is also
                 optional, and defaults to {default_pickle}.
                 N.b.: don't do this with -k csv

  write_csv - write out a CSV file.  Each line contains the time zone
              name and a list of floats for a single polygon in that
              time zone.  <input_path> is as with test.  <output_path>
              is also optional, and defaults to {default_csv}.
              N.b.: don't do this with -k csv

Options:
  -k <kind>, --kind=<kind>  Input kind. Should be json or csv or pickle
                            [default: json].
  -m, --memory              Report on memory usage before, during, and
                            after operation.
  -h, --help                Show this help.

""".format(**{
    'default_json': tzwhere.DEFAULT_JSON,
    'default_pickle': tzwhere.DEFAULT_PICKLE,
    'default_csv': tzwhere.DEFAULT_CSV,
})


report_memory = False


def main():
    try:
        import docopt
    except ImportError:
        print("Please install the docopt package to use tzwhere.py as a script.")
        import sys
        sys.exit(1)

    args = docopt.docopt(HELP)

    global report_memory
    report_memory = args['--memory']

    if args['test']:
        test(args['--kind'], args['<input_path>'])
    elif args['write_pickle']:
        if args['--kind'] not in ('json', 'pickle'):
            print "Can't write pickle output from CSV input"
            return
        if args['<output_path>'] is None:
            args['<output_path>'] = tzwhere.DEFAULT_PICKLE
        write_pickle(args['--kind'], args['<input_path>'],
                     args['<output_path>'])
    elif args['write_csv']:
        if args['--kind'] not in ('json', 'pickle'):
            print "Can't write CSV output from CSV input"
            return
        if args['<output_path>'] is None:
            args['<output_path>'] = tzwhere.DEFAULT_CSV
        write_csv(args['--kind'], args['<input_path>'],
                  args['<output_path>'])


def test(input_kind, path):
    memuse()
    start = datetime.datetime.now()
    w = tzwhere(input_kind, path)
    end = datetime.datetime.now()
    print 'Initialized in: ',
    print end - start
    memuse()
    template = '{0:20s} | {1:20s} | {2:20s} | {3:2s}'
    print(template.format('LOCATION', 'EXPECTED', 'COMPUTED', '=='))
    TEST_LOCATIONS = (
        ( 35.295953,  -89.662186,  'Arlington, TN',        'America/Chicago'),
        ( 33.58,      -85.85,      'Memphis, TN',          'America/Chicago'),
        ( 61.17,     -150.02,      'Anchorage, AK',        'America/Anchorage'),
        ( 44.12,     -123.22,      'Eugene, OR',           'America/Los_Angeles'),
        ( 42.652647,  -73.756371,  'Albany, NY',           'America/New_York'),
        ( 55.743749,   37.6207923, 'Moscow',               'Europe/Moscow'),
        ( 34.104255, -118.4055591, 'Los Angeles',          'America/Los_Angeles'),
        ( 55.743749,   37.6207923, 'Moscow',               'Europe/Moscow'),
        ( 39.194991, -106.8294024, 'Aspen, Colorado',      'America/Denver'),
        ( 50.438114,   30.5179595, 'Kiev',                 'Europe/Kiev'),
        ( 12.936873,   77.6909136, 'Jogupalya',            'Asia/Kolkata'),
        ( 38.889144,  -77.0398235, 'Washington DC',        'America/New_York'),
        ( 59.932490,   30.3164291, 'St Petersburg',        'Europe/Moscow'),
        ( 50.300624,  127.559166,  'Blagoveshchensk',      'Asia/Yakutsk'),
        ( 42.439370,  -71.0700416, 'Boston',               'America/New_York'),
        ( 41.84937,   -87.6611995, 'Chicago',              'America/Chicago'),
        ( 28.626873,  -81.7584514, 'Orlando',              'America/New_York'),
        ( 47.610615, -122.3324847, 'Seattle',              'America/Los_Angeles'),
        ( 51.499990,   -0.1353549, 'London',               'Europe/London'),
        ( 51.256241,   -0.8186531, 'Church Crookham',      'Europe/London'),
        ( 51.292215,   -0.8002638, 'Fleet',                'Europe/London'),
        ( 48.868743,    2.3237586, 'Paris',                'Europe/Paris'),
        ( 22.158114,  113.5504603, 'Macau',                'Asia/Macau'),
        ( 56.833123,   60.6097054, 'Russia',               'Asia/Yekaterinburg'),
        ( 60.887496,   26.6375756, 'Salo',                 'Europe/Helsinki'),
        ( 52.799992,   -1.8524408, 'Staffordshire',        'Europe/London'),
        (  5.016666,  115.0666667, 'Muara',                'Asia/Brunei'),
        (-41.466666,  -72.95,      'Puerto Montt seaport', 'America/Santiago'),
        ( 34.566666,   33.0333333, 'Akrotiri seaport',     'Asia/Nicosia'),
        ( 37.466666,  126.6166667, 'Inchon seaport',       'Asia/Seoul'),
        ( 42.8,       132.8833333, 'Nakhodka seaport',     'Asia/Vladivostok'),
        ( 50.26,       -5.051,     'Truro',                'Europe/London'),
        ( 50.26,       -8.051,     'Sea off Cornwall',     None)
    )
    for (lat, lon, loc, expected) in TEST_LOCATIONS:
        computed = w.tzNameAt(float(lat), float(lon))
        ok = 'OK' if computed == expected else 'XX'
        print(template.format(loc, expected, computed, ok))
    memuse()


def write_pickle(input_kind, input_path, output_path):
    memuse()
    features = tzwhere.read_tzworld(input_kind, input_path)
    memuse()
    tzwhere.write_pickle(features, output_path)
    memuse()


def write_csv(input_kind, input_path, output_path):
    memuse()
    features = tzwhere.read_tzworld(input_kind, input_path)
    memuse()
    tzwhere.write_csv(features, output_path)
    memuse()


def memuse():
    global report_memory
    if not report_memory:
        return

    import subprocess
    import resource

    free = int(subprocess.check_output(['free', '-m']
                                   ).split('\n')[2].split()[-1])
    maxrss = resource.getrusage(
        resource.RUSAGE_SELF).ru_maxrss / 1000
    print
    print 'Memory:'
    print '{0:6d} MB free'.format(free)
    print '{0:6d} MB maxrss'.format(maxrss)
    print

if __name__ == "__main__":
    main()
