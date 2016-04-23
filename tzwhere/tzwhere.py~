#!/usr/bin/env python

"""tzwhere.py - time zone computation from latitude/longitude.

Ordinarily this is loaded as a module and instances of the tzwhere
class are instantiated and queried directly, but the module can be run
as a script too (this requires the docopt package to be installed).
Run it with the -h option to see usage.

"""

import csv
import collections
try:
    import json
except ImportError:
    import simplejson as json
import math
import os
import pickle
import logging

# We can speed up things by about 200 times if we use shapely
try:
    from shapely.geometry import Polygon, Point
    from shapely.prepared import prep
    SHAPELY_IMPORT = True
except ImportError:
    SHAPELY_IMPORT = False

# We can save about 222MB of RAM by turning our polygon lists into
# numpy arrays rather than tuples, if numpy is installed.
try:
    import numpy
    WRAP = numpy.array
except ImportError:
    WRAP = tuple

LOGGER = logging.getLogger('pytzwhere')


class tzwhere(object):

    SHORTCUT_DEGREES_LATITUDE = 1
    SHORTCUT_DEGREES_LONGITUDE = 1
    # By default, use the data file in our package directory
    DEFAULT_JSON = os.path.join(os.path.dirname(__file__),
                                'tz_world.json')

    def __init__(self, input_kind='csv', path=None,
                 shapely=False, forceTZ=False):
        '''
        Initializes the tzwhere class.
        @input_kind: Which filetype you want to read from
        @path: Where you want to read the input file from
        @shapely: Whether you want to use shapely to represent the geometry.
        Lookups become much faster at the cost of a slower initialization
        @forceTZ: If you want to force the lookup method to a return a
        timezone even if the point you are looking up is slightly outside it's
        bounds, you need to specify this during initialization arleady
        '''

        if (shapely or forceTZ) and not SHAPELY_IMPORT:
            raise ValueError('You need to have shapley installed for this '
                             'feature, but we can\'t find it')
        if not shapely and forceTZ:
            raise ValueError('The lookup \'hack\' depends on shapely. Try using'
                             ' shapely=True when initializing the class')

        self.forceTZ = forceTZ
        self.shapely = shapely and SHAPELY_IMPORT

        # Construct appropriate generator for (tz, polygon) pairs.
        if input_kind in ['json']:
            featureCollection = tzwhere.read_tzworld(input_kind, path)
            pgen = tzwhere._feature_collection_polygons(featureCollection)
        else:
            raise ValueError(input_kind)

        # Turn that into an internal mapping
        if self.shapely:
            self._construct_shapely_map(pgen, forceTZ)
        else:
            self._construct_polygon_map(pgen)

        # Convert polygon lists to numpy arrays or (failing that)
        # tuples to save memory.
        for tzname in self.timezoneNamesToPolygons.keys():
            self.timezoneNamesToPolygons[tzname] = \
                WRAP(self.timezoneNamesToPolygons[tzname])

        # And construct lookup shortcuts.
        self._construct_shortcuts()

    def _construct_shapely_map(self, polygon_generator, forceTZ):
        """Turn a (tz, polygon) generator, into our internal shapely mapping."""
        self.timezoneNamesToPolygons = collections.defaultdict(list)
        self.unprepTimezoneNamesToPolygons = collections.defaultdict(list)

        for (tzname, poly) in polygon_generator:
            poly = Polygon(poly)
            self.timezoneNamesToPolygons[tzname].append(
                prep(poly))
            if forceTZ:
                self.unprepTimezoneNamesToPolygons[tzname].append(
                    poly)

    def _construct_polygon_map(self, polygon_generator):
        """Turn a (tz, polygon) generator, into our internal mapping."""
        self.timezoneNamesToPolygons = collections.defaultdict(list)
        for (tzname, poly) in polygon_generator:
            self.timezoneNamesToPolygons[tzname].append(
                WRAP(poly))

    def _construct_shortcuts(self):
        ''' Construct our shortcuts for looking up polygons. Much faster
        than using an r-tree '''
        self.timezoneLongitudeShortcuts = {}
        self.timezoneLatitudeShortcuts = {}

        for tzname in self.timezoneNamesToPolygons:
            for polyIndex, poly in enumerate(self.timezoneNamesToPolygons[tzname]):
                if self.shapely:
                    lngs = [x[0] for x in poly.context.exterior.coords]
                    lats = [x[1] for x in poly.context.exterior.coords]
                else:
                    lngs = [x[0] for x in poly]
                    lats = [x[1] for x in poly]
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

    def tzNameAt(self, latitude, longitude, forceTZ=False):
        '''
        Let's you lookup for a given latitude and longitude the appropriate
        timezone.
        @latitude: latitude
        @longitude: longitude
        @forceTZ: If forceTZ is true and you can't find a valid timezone return
        the closest timezone you can find instead. Only works if the point is
        reasonable close to a timezone already. Consider this a somewhat of a
        'hack'. Introduces potential errors, be warned.

        '''

        if forceTZ and not self.forceTZ:
            raise ValueError('You need to initialize the class with forceTZ='
                             'True if you want to use it later on during the'
                             ' lookup')

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

        if self.shapely:
            queryPoint = Point(longitude, latitude)

        if possibleTimezones:
            for tzname in possibleTimezones:
                polyIndices = set(latTzOptions[tzname]).intersection(set(lngTzOptions[tzname]))
                for polyIndex in polyIndices:
                    poly = self.timezoneNamesToPolygons[tzname][polyIndex]
                    if self.shapely:
                        if poly.contains_properly(queryPoint):
                            return tzname
                    else:
                        if self._point_inside_polygon(latitude,longitude, poly):
                            return tzname
        distances = []
        if forceTZ:
            if possibleTimezones:
                if len(possibleTimezones) == 1:
                    return possibleTimezones.pop()
                else:
                    for tzname in possibleTimezones:
                        polyIndices = set(latTzOptions[tzname]).intersection(set(lngTzOptions[tzname]))
                        for polyIndex in polyIndices:
                            poly = self.unprepTimezoneNamesToPolygons[tzname][polyIndex]
                            d = poly.distance(queryPoint)
                            distances.append((d, tzname))
            if len(distances) > 0:
                return sorted(distances, key=lambda x: x[1])[0][1]

    @staticmethod
    def _point_inside_polygon(x, y, poly):
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

    @staticmethod
    def read_tzworld(input_kind='json', path=None):
        reader = tzwhere.read_json if input_kind == 'json' else tzwhere.read_pickle
        return reader(path)

    @staticmethod
    def read_json(path=None):
        if path is None:
            path = tzwhere.DEFAULT_JSON
        LOGGER.info('Reading json input file: %s\n' % path)
        with open(path, 'r') as f:
            featureCollection = json.load(f)
        return featureCollection

    @staticmethod
    def _feature_collection_polygons(featureCollection):
        """Turn a feature collection that you get from a pickle
        into an iterator over polygons.

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


def main():
    print('Usage of pytzwhere as a script is no longer supported. Please use version 2.3')

if __name__ == "__main__":
    main()
