#!/usr/bin/env python

"""tzwhere.py - time zone computation from latitude/longitude.

Ordinarily this is loaded as a module and instances of the tzwhere
class are instantiated and queried directly, but the module can be run
as a script too, in which case it operates as follows:

Usage:
  tzwhere.py [options] test
  tzwhere.py [options] write-pickle [<write_pickle_path>]

Modes:

  test - try out a few test locations

  write-pickle - write out a pickle file; the output pickle file path
      can be specified but is optional, and defaults to the same
      default value as the --pickle_file option.

Options:
  --json_file=<file>    Path to the json input file [default: tz_world_compact.json].
  --pickle_file=<file>  Path to the pickle input file [default: tz_world.pickle].
  --read_pickle         Read pickle data instead of json [default: False].
  -h, --help            Show this help.

"""

try:
    import json
except ImportError:
    import simplejson as json
import datetime
import math
import os
import pickle


class tzwhere(object):

    SHORTCUT_DEGREES_LATITUDE = 1
    SHORTCUT_DEGREES_LONGITUDE = 1
    # By default, use the data file in our package directory
    DEFAULT_JSON = os.path.join(os.path.dirname(__file__),
        'tz_world_compact.json')
    DEFAULT_PICKLE = os.path.join(os.path.dirname(__file__),
        'tz_world.pickle')

    def __init__(self, filename=None, read_pickle=False):

        featureCollection = tzwhere.read_tzworld(filename, read_pickle)

        self._construct_polygon_map(featureCollection)
        self._construct_shortcuts()

    def _construct_polygon_map(self, featureCollection):

        self.timezoneNamesToPolygons = {}
        for feature in featureCollection['features']:

            tzname = feature['properties']['TZID']
            if feature['geometry']['type'] == 'Polygon':
                polys = feature['geometry']['coordinates']
                if polys and not (tzname in self.timezoneNamesToPolygons):
                    self.timezoneNamesToPolygons[tzname] = []

                for raw_poly in polys:
                    # WPS84 coordinates are [long, lat], while many
                    # conventions are [lat, long] Our data is in
                    # WPS84.  Convert to an explicit format which
                    # geolib likes.
                    assert len(raw_poly) % 2 == 0
                    poly = []
                    while raw_poly:
                        lat = raw_poly.pop()
                        lng = raw_poly.pop()
                        poly.append({'lat': lat, 'lng': lng})
                    self.timezoneNamesToPolygons[tzname].append(tuple(poly))

        # Convert things to tuples to save memory
        for tzname in self.timezoneNamesToPolygons.keys():
            self.timezoneNamesToPolygons[tzname] = \
                tuple(self.timezoneNamesToPolygons[tzname])

    def _construct_shortcuts(self):

        self.timezoneLongitudeShortcuts = {}
        self.timezoneLatitudeShortcuts = {}
        for tzname in self.timezoneNamesToPolygons:
            for polyIndex, poly in enumerate(self.timezoneNamesToPolygons[tzname]):
                lats = [x['lat'] for x in poly]
                lngs = [x['lng'] for x in poly]
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

        p1x, p1y = poly[0]['lng'], poly[0]['lat']
        for i in range(n + 1):
            p2x, p2y = poly[i % n]['lng'], poly[i % n]['lat']
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
    def read_tzworld(filename=None, read_pickle=False):
        reader = tzwhere.read_json if not read_pickle else tzwhere.read_pickle
        return reader(filename)

    @staticmethod
    def read_json(path=DEFAULT_JSON):
        print('Reading json input file: %s' % path)
        with open(path, 'r') as f:
            featureCollection = json.load(f)
        return featureCollection

    @staticmethod
    def read_pickle(path=DEFAULT_PICKLE):
        print('Reading pickle input file: %s' % path)
        with open(path, 'r') as f:
            featureCollection = pickle.load(f)
        return featureCollection

    @staticmethod
    def write_pickle(featureCollection, path=DEFAULT_PICKLE):
        print 'Writing pickle output file: %s' % path
        with open(path, 'w') as f:
            pickle.dump(featureCollection, f, pickle.HIGHEST_PROTOCOL)


def main():
    try:
        import docopt
    except ImportError:
        print("Please install the docopt package to use tzwhere.py as a script.")
        import sys
        sys.exit(1)

    args = docopt.docopt(__doc__)

    if args['--read_pickle']:
        filename = args['--pickle_file']
    else:
        filename = args['--json_file']

    if args['test']:
        test(filename, args['--read_pickle'])
    elif args['write-pickle']:
        if args['<write_pickle_path>'] is None:
            args['<write_pickle_path>'] = tzwhere.DEFAULT_PICKLE
        write_pickle(filename, args['--read_pickle'],
                     args['<write_pickle_path>'])


def test(filename=None, read_pickle=False):
    start = datetime.datetime.now()
    w = tzwhere(filename, read_pickle)  # XXX None
    end = datetime.datetime.now()
    print 'Initialized in: ',
    print end - start
    for (lat, lon, loc, expected) in (
        (35.295953, -89.662186, 'Arlington, TN', 'America/Chicago'),
        (33.58,     -85.85,     'Memphis, TN',   'America/Chicago'),
        (61.17,     -150.02,    'Anchorage, AK', 'America/Anchorage'),
        (44.12,     -123.22,    'Eugene, OR',    'America/Los_Angeles'),
        (42.652647, -73.756371, 'Albany, NY',    'America/New_York'),
    ):
        actual = w.tzNameAt(float(lat), float(lon))
        ok = 'OK' if actual == expected else 'XX'
        print('{0} | {1:20s} | {2:20s} | {3:20s}'.format(
            ok, loc, actual, expected))


def write_pickle(filename, read_pickle, write_pickle_path):
    tzwhere.write_pickle(tzwhere.read_tzworld(filename, read_pickle),
                         write_pickle_path)


if __name__ == "__main__":
    main()
