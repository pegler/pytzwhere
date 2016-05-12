#!/usr/bin/env python

'''tzwhere.py - time zone computation from latitude/longitude.

Ordinarily this is loaded as a module and instances of the tzwhere
class are instantiated and queried directly
'''

import collections
try:
    import json
except ImportError:
    import simplejson as json
import math
import numpy
import os
import shapely as shp


class tzwhere(object):

    SHORTCUT_DEGREES_LATITUDE = 1
    SHORTCUT_DEGREES_LONGITUDE = 1
    # By default, use the data file in our package directory
    DEFAULT_SHORTCUTS = os.path.join(os.path.dirname(__file__),
                                     'tz_world_shortcuts.json')
    DEFAULT_POLYGONS = os.path.join(os.path.dirname(__file__),
                                    'tz_world.json')

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
            self.timezoneNamesToPolygons[tzname] = \
                numpy.asarray(polys)
            if forceTZ:
                for poly in polys:
                    self.unprepTimezoneNamesToPolygons[tzname].append(
                        shp.Polygon(poly[0], poly[1]))

        with open(tzwhere.DEFAULT_SHORTCUTS, 'r') as f:
            self.timezoneLongitudeShortcuts,\
                self.timezoneLatitudeShortcuts = json.load(f)

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

        if forceTZ:
            assert self.forceTZ, 'You need to initialize tzwhere with forceTZ\
                if you want to use the lookup workaround'

        latTzOptions = self.timezoneLatitudeShortcuts[str(
            (math.floor(latitude / self.SHORTCUT_DEGREES_LATITUDE) *
             self.SHORTCUT_DEGREES_LATITUDE))
        ]
        latSet = set(latTzOptions.keys())
        lngTzOptions = self.timezoneLongitudeShortcuts[str(
            (math.floor(longitude / self.SHORTCUT_DEGREES_LONGITUDE) *
             self.SHORTCUT_DEGREES_LONGITUDE))
        ]
        lngSet = set(lngTzOptions.keys())
        possibleTimezones = lngSet.intersection(latSet)

        queryPoint = shp.Point(longitude, latitude)

        if possibleTimezones:
            for tzname in possibleTimezones:
                if isinstance(self.timezoneNamesToPolygons[tzname],
                              numpy.ndarray):
                    self.timezoneNamesToPolygons[tzname] = list(
                        map(lambda p: shp.prepared.prep(
                            shp.Polygon(p[0], p[1])),
                            self.timezoneNamesToPolygons[tzname]))
                polyIndices = set(latTzOptions[tzname]).intersection(set(
                    lngTzOptions[tzname]))
                for polyIndex in polyIndices:
                    poly = self.timezoneNamesToPolygons[tzname][polyIndex]
                    if poly.contains_properly(queryPoint):
                        return tzname

        if forceTZ:
            self.__forceTZ__(possibleTimezones, latTzOptions,
                             lngTzOptions, queryPoint)

    def __forceTZ__(self, possibleTimezones, latTzOptions,
                    lngTzOptions, queryPoint):
        distances = []
        if possibleTimezones:
            if len(possibleTimezones) == 1:
                return possibleTimezones.pop()
            else:
                for tzname in possibleTimezones:
                    polyIndices = set(latTzOptions[tzname]).intersection(
                        set(lngTzOptions[tzname]))
                    for polyIndex in polyIndices:
                        poly = self.unprepTimezoneNamesToPolygons[
                            tzname][polyIndex]
                        d = poly.distance(queryPoint)
                        distances.append((d, tzname))
        if len(distances) > 0:
            return sorted(distances, key=lambda x: x[1])[0][1]


class prepareMap(object):

    def __init__(self):
        featureCollection = read_tzworld('tz_world.json')
        pgen = feature_collection_polygons(featureCollection)
        tzNamesToPolygons = collections.defaultdict(list)
        for tzname, poly in pgen:
            tzNamesToPolygons[tzname].append(poly)

        for tzname, polys in tzNamesToPolygons.items():
            tzNamesToPolygons[tzname] = \
                numpy.asarray(tzNamesToPolygons[tzname])

        timezoneLongitudeShortcuts,\
            timezoneLatitudeShortcuts = self.construct_shortcuts(
                tzNamesToPolygons, tzwhere.SHORTCUT_DEGREES_LONGITUDE,
                tzwhere.SHORTCUT_DEGREES_LATITUDE)

        with open('tz_world_shortcuts.json', 'w') as f:
            json.dump((timezoneLongitudeShortcuts,
                      timezoneLatitudeShortcuts), f)

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

        # Convert things to tuples to save memory
        for degree in timezoneLatitudeShortcuts:
            for tzname in timezoneLatitudeShortcuts[degree].keys():
                timezoneLatitudeShortcuts[degree][tzname] = \
                    tuple(timezoneLatitudeShortcuts[degree][tzname])
        for degree in timezoneLongitudeShortcuts.keys():
            for tzname in timezoneLongitudeShortcuts[degree].keys():
                timezoneLongitudeShortcuts[degree][tzname] = \
                    tuple(timezoneLongitudeShortcuts[degree][tzname])
        return timezoneLongitudeShortcuts, timezoneLatitudeShortcuts


def read_tzworld(path):
    reader = read_json
    return reader(path)


def read_json(path):
    with open(path, 'r') as f:
        featureCollection = json.load(f)
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
