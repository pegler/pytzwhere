#!/usr/bin/env python

"""tzwhere.py - time zone computation from latitude/longitude.

Ordinarily this is loaded as a module and instances of the tzwhere
class are instantiated and queried directly, but the module can be run
as a script too (this requires the docopt package to be installed).
Run it with the -h option to see usage.

"""
from shapely.geometry import Polygon, Point
from shapely.prepared import prep

import collections
try:
    import json
except ImportError:
    import simplejson as json
import math
import numpy
import os


class tzwhere(object):

    SHORTCUT_DEGREES_LATITUDE = 1
    SHORTCUT_DEGREES_LONGITUDE = 1
    # By default, use the data file in our package directory
    DEFAULT_JSON = os.path.join(os.path.dirname(__file__),
                                'tz_world.json')

    def __init__(self, path=None, shapely=False, forceTZ=False):
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

        self.forceTZ = forceTZ

        # Construct appropriate generator for (tz, polygon) pairs.
        featureCollection = tzwhere.read_tzworld(path)
        pgen = tzwhere._feature_collection_polygons(featureCollection)

        # Turn that into an internal mapping
        self._construct_shapely_map(pgen, forceTZ)

        # Convert polygon lists to numpy arrays
        for tzname in self.timezoneNamesToPolygons.keys():
            self.timezoneNamesToPolygons[tzname] = \
                numpy.asarray(self.timezoneNamesToPolygons[tzname])

        # And construct lookup shortcuts.
        self._construct_shortcuts()

    def _construct_shapely_map(self, polygon_generator, forceTZ):
        """Turn a (tz, polygon) generator, into our internal shapely mapping."""
        self.timezoneNamesToPolygons = collections.defaultdict(list)
        self.unprepTimezoneNamesToPolygons = collections.defaultdict(list)

        for (tzname, poly) in polygon_generator:
            self.timezoneNamesToPolygons[tzname].append(
                poly)
            if forceTZ:
                self.unprepTimezoneNamesToPolygons[tzname].append(
                    poly)

    def _construct_shortcuts(self):
        ''' Construct our shortcuts for looking up polygons. Much faster
        than using an r-tree '''
        self.timezoneLongitudeShortcuts = {}
        self.timezoneLatitudeShortcuts = {}

        for tzname in self.timezoneNamesToPolygons:
            for polyIndex, poly in enumerate(self.timezoneNamesToPolygons[tzname]):
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

        queryPoint = Point(longitude, latitude)

        if possibleTimezones:
            for tzname in possibleTimezones:
                # TODO this isinstance is not implemented correctly
                if isinstance(self.timezoneNamesToPolygons[tzname], numpy.ndarray):
                    self.timezoneNamesToPolygons[tzname] = list(map(lambda p: prep(Polygon(p)), self.timezoneNamesToPolygons[tzname]))
                polyIndices = set(latTzOptions[tzname]).intersection(set(lngTzOptions[tzname]))
                for polyIndex in polyIndices:
                    poly = self.timezoneNamesToPolygons[tzname][polyIndex]
                    if poly.contains_properly(queryPoint):
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
    def read_tzworld(path=None):
        reader = tzwhere.read_json
        return reader(path)

    @staticmethod
    def read_json(path=None):
        if path is None:
            path = tzwhere.DEFAULT_JSON
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
    print('We have to implement a rewrite of that')

if __name__ == "__main__":
    main()
