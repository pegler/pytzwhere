#!/usr/bin/env python

'''tzwhere.py - time zone computation from latitude/longitude.

Ordinarily this is loaded as a module and instances of the tzwhere
class are instantiated and queried directly
'''

import collections
try:
    import ujson as json # loads 2 seconds faster than normal json
except:
    try:
        import json
    except ImportError:
        import simplejson as json
import math
import gzip
import os
import shapely.geometry as geometry
import shapely.prepared as prepared

# We can save about 222MB of RAM by turning our polygon lists into
# numpy arrays rather than tuples, if numpy is installed.
try:
    import numpy
    WRAP = numpy.asarray
    COLLECTION_TYPE = numpy.ndarray
except ImportError:
    WRAP = tuple
    COLLECTION_TYPE = tuple

# for navigation and pulling values/files
this_dir, this_filename = os.path.split(__file__)
BASE_DIR = os.path.dirname(this_dir)

class tzwhere(object):

    SHORTCUT_DEGREES_LATITUDE = 1.0
    SHORTCUT_DEGREES_LONGITUDE = 1.0
    # By default, use the data file in our package directory
    DEFAULT_SHORTCUTS = os.path.join(os.path.dirname(__file__),
                                     'tz_world_shortcuts.json')
    DEFAULT_POLYGONS = os.path.join(os.path.dirname(__file__),
                                    'tz_world.json.gz')

    def __init__(self, forceTZ=False):
        '''
        Initializes the tzwhere class.
        @forceTZ: If you want to force the lookup method to a return a
        timezone even if the point you are looking up is slightly outside it's
        bounds, you need to specify this during initialization arleady
        '''

        featureCollection = read_tzworld(tzwhere.DEFAULT_POLYGONS)
        pgen = feature_collection_polygons(featureCollection)
        self.timezoneNamesToPolygons = collections.defaultdict(list)
        self.unprepTimezoneNamesToPolygons = collections.defaultdict(list)
        for tzname, poly in pgen:
            self.timezoneNamesToPolygons[tzname].append(poly)
        for tzname, polys in self.timezoneNamesToPolygons.items():
            self.timezoneNamesToPolygons[tzname] = WRAP(polys)

            if forceTZ:
                self.unprepTimezoneNamesToPolygons[tzname] = WRAP(polys)

        with open(tzwhere.DEFAULT_SHORTCUTS, 'r') as f:
            self.timezoneLongitudeShortcuts, self.timezoneLatitudeShortcuts = json.load(f)

        self.forceTZ = forceTZ
        for tzname in self.timezoneNamesToPolygons:
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
        the closest timezone you can find instead. Only works if the point has
        the same integer value for its degree than the timezeone
        '''

        if forceTZ:
            assert self.forceTZ, 'You need to initialize tzwhere with forceTZ'

        latTzOptions = self.timezoneLatitudeShortcuts[str(
            (math.floor(latitude / self.SHORTCUT_DEGREES_LATITUDE) *
             self.SHORTCUT_DEGREES_LATITUDE)
        )]
        latSet = set(latTzOptions.keys())
        lngTzOptions = self.timezoneLongitudeShortcuts[str(
            (math.floor(longitude / self.SHORTCUT_DEGREES_LONGITUDE) *
             self.SHORTCUT_DEGREES_LONGITUDE)
        )]
        lngSet = set(lngTzOptions.keys())
        possibleTimezones = lngSet.intersection(latSet)

        queryPoint = geometry.Point(longitude, latitude)

        if possibleTimezones:
            for tzname in possibleTimezones:
                if isinstance(self.timezoneNamesToPolygons[tzname], COLLECTION_TYPE):
                    self.timezoneNamesToPolygons[tzname] = list(
                        map(lambda p: prepared.prep(
                                geometry.Polygon(p[0], p[1])
                            ), self.timezoneNamesToPolygons[tzname]))

                polyIndices = set(latTzOptions[tzname]).intersection(set(
                    lngTzOptions[tzname]
                ))

                for polyIndex in polyIndices:
                    poly = self.timezoneNamesToPolygons[tzname][polyIndex]
                    if poly.contains_properly(queryPoint):
                        return tzname

        if forceTZ:
            return self.__forceTZ__(possibleTimezones, latTzOptions,
                             lngTzOptions, queryPoint)

    def __forceTZ__(self, possibleTimezones, latTzOptions,
                    lngTzOptions, queryPoint):
        distances = []
        if possibleTimezones:
            if len(possibleTimezones) == 1:
                return possibleTimezones.pop()
            else:
                for tzname in possibleTimezones:
                    if isinstance(self.unprepTimezoneNamesToPolygons[tzname],
                                  COLLECTION_TYPE):
                        self.unprepTimezoneNamesToPolygons[tzname] = list(
                            map(lambda p: p.context if isinstance(p, prepared.PreparedGeometry) else geometry.Polygon(p[0], p[1]),
                                self.timezoneNamesToPolygons[tzname]))
                    polyIndices = set(latTzOptions[tzname]).intersection(
                        set(lngTzOptions[tzname]))
                    for polyIndex in polyIndices:
                        poly = self.unprepTimezoneNamesToPolygons[
                            tzname][polyIndex]
                        d = poly.distance(queryPoint)
                        distances.append((d, tzname))
        if len(distances) > 0:
            return sorted(distances, key=lambda x: x[0])[0][1]


class prepareMap(object):

    def __init__(self):
        DEFAULT_SHORTCUTS = os.path.join(os.path.dirname(__file__),
                                         'tz_world_shortcuts.json')
        DEFAULT_POLYGONS = os.path.join(os.path.dirname(__file__),
                                        'tz_world.json.gz')
        featureCollection = read_tzworld(DEFAULT_POLYGONS)
        pgen = feature_collection_polygons(featureCollection)
        tzNamesToPolygons = collections.defaultdict(list)
        for tzname, poly in pgen:
            tzNamesToPolygons[tzname].append(poly)

        for tzname, polys in tzNamesToPolygons.items():
            tzNamesToPolygons[tzname] = \
                WRAP(tzNamesToPolygons[tzname])

        timezoneLongitudeShortcuts,\
            timezoneLatitudeShortcuts = self.construct_shortcuts(
                tzNamesToPolygons, tzwhere.SHORTCUT_DEGREES_LONGITUDE,
                tzwhere.SHORTCUT_DEGREES_LATITUDE)

        with open(DEFAULT_SHORTCUTS, 'w') as f:
            json.dump(
                (timezoneLongitudeShortcuts, timezoneLatitudeShortcuts), f)

    @staticmethod
    def construct_shortcuts(timezoneNamesToPolygons,
                            shortcut_long, shortcut_lat):
        ''' Construct our shortcuts for looking up polygons. Much faster
        than using an r-tree '''

        def find_min_max(ls, gridSize):
            minLs = (math.floor(min(ls) / gridSize) *
                     gridSize)
            maxLs = (math.floor(max(ls) / gridSize) *
                     gridSize)
            return minLs, maxLs

        timezoneLongitudeShortcuts = {}
        timezoneLatitudeShortcuts = {}

        for tzname in timezoneNamesToPolygons:
            tzLngs = []
            tzLats = []
            for polyIndex, poly in enumerate(timezoneNamesToPolygons[tzname]):
                lngs = [x[0] for x in poly[0]]
                lats = [x[1] for x in poly[0]]
                tzLngs.extend(lngs)
                tzLats.extend(lats)
                minLng, maxLng = find_min_max(
                    lngs, shortcut_long)
                minLat, maxLat = find_min_max(
                    lats, shortcut_lat)
                degree = minLng

                while degree <= maxLng:
                    if degree not in timezoneLongitudeShortcuts:
                        timezoneLongitudeShortcuts[degree] =\
                            collections.defaultdict(list)
                    timezoneLongitudeShortcuts[degree][tzname].append(polyIndex)
                    degree = degree + shortcut_long

                degree = minLat
                while degree <= maxLat:
                    if degree not in timezoneLatitudeShortcuts:
                        timezoneLatitudeShortcuts[degree] =\
                            collections.defaultdict(list)
                    timezoneLatitudeShortcuts[degree][tzname].append(polyIndex)
                    degree = degree + shortcut_lat
        return timezoneLongitudeShortcuts, timezoneLatitudeShortcuts


def read_tzworld(path):
    reader = read_json
    return reader(path)


def read_json(path):
    with gzip.open(path, "rb") as f:
        featureCollection = json.loads(f.read().decode("utf-8"))
    return featureCollection


def feature_collection_polygons(featureCollection):
    """Turn a feature collection
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
            exterior = feature['geometry']['coordinates'][0]
            interior = feature['geometry']['coordinates'][1:]
            yield (tzname, (exterior, interior))

if __name__ == "__main__":
    prepareMap()
