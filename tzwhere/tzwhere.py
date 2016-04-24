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
import pickle


class tzwhere(object):

    SHORTCUT_DEGREES_LATITUDE = 1
    SHORTCUT_DEGREES_LONGITUDE = 1
    # By default, use the data file in our package directory
    DEFAULT_SHORTCUTS = os.path.join(os.path.dirname(__file__),
                                     'tz_world_shortcuts.pck')
    DEFAULT_POLYGONS = os.path.join(os.path.dirname(__file__),
                                    'tz_world_polygons.pck')

    def __init__(self, path=None, shapely=False, forceTZ=False, gridSize=1):
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
        with open(tzwhere.DEFAULT_SHORTCUTS, 'rb') as f:
            self.timezoneLongitudeShortcuts,\
                self.timezoneLatitudeShortcuts = pickle.load(f)

        with open(tzwhere.DEFAULT_POLYGONS, 'rb') as f:
            self.timezoneNamesToPolygons = pickle.load(f)

    def tzNameAt(self, latitude, longitude):
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

        latTzOptions = self.timezoneLatitudeShortcuts[
            (math.floor(latitude / self.SHORTCUT_DEGREES_LATITUDE) *
             self.SHORTCUT_DEGREES_LATITUDE)
        ]
        latSet = set(latTzOptions.keys())
        lngTzOptions = self.timezoneLongitudeShortcuts[
            (math.floor(longitude / self.SHORTCUT_DEGREES_LONGITUDE) *
             self.SHORTCUT_DEGREES_LONGITUDE)
        ]
        lngSet = set(lngTzOptions.keys())
        possibleTimezones = lngSet.intersection(latSet)

        queryPoint = Point(longitude, latitude)

        if possibleTimezones:
            for tzname in possibleTimezones:
                if isinstance(self.timezoneNamesToPolygons[tzname],
                              numpy.ndarray):
                    self.timezoneNamesToPolygons[tzname] = list(
                        map(lambda p: prep(Polygon(p[0], p[1])),
                        self.timezoneNamesToPolygons[tzname]))
                polyIndices = set(latTzOptions[tzname]).intersection(set(lngTzOptions[tzname]))
                for polyIndex in polyIndices:
                    poly = self.timezoneNamesToPolygons[tzname][polyIndex]
                    if poly.contains_properly(queryPoint):
                        return tzname

    @staticmethod
    def read_tzworld(path):
        reader = tzwhere.read_json
        return reader(path)

    @staticmethod
    def read_json(path):
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
                exterior = feature['geometry']['coordinates'][0]
                interior = feature['geometry']['coordinates'][1:]
                yield (tzname, (exterior, interior))


def _construct_shapely_map(polygon_generator):
    """Turn a (tz, polygon) generator, into our internal shapely mapping."""
    timezoneNamesToPolygons = collections.defaultdict(list)
    for (tzname, poly) in polygon_generator:
        timezoneNamesToPolygons[tzname].append(
            poly)
    return timezoneNamesToPolygons

def _construct_shortcuts(timezoneNamesToPolygons,
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
            minLng, maxLng = find_min_max(lngs,
                                          shortcut_long)
            minLat, maxLat = find_min_max(lats,
                                          shortcut_lat)
            degree = minLng

            while degree <= maxLng:
                if degree not in timezoneLongitudeShortcuts:
                    timezoneLongitudeShortcuts[degree] = {}

                if tzname not in timezoneLongitudeShortcuts[degree]:
                    timezoneLongitudeShortcuts[degree][tzname] = []

                timezoneLongitudeShortcuts[degree][tzname].append(polyIndex)
                degree = degree + shortcut_long

            degree = minLat
            while degree <= maxLat:
                if degree not in timezoneLatitudeShortcuts:
                    timezoneLatitudeShortcuts[degree] = {}

                if tzname not in timezoneLatitudeShortcuts[degree]:
                    timezoneLatitudeShortcuts[degree][tzname] = []

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


def main():

    def intCast(x):
        return (int(x[0] * 10000000), int(x[1] * 10000000))

    from shapely.geometry import box, Polygon, MultiPolygon, GeometryCollection

    def katana(geometry, threshold, count=0):
        """Split a Polygon into two parts across it's shortest dimension"""
        bounds = geometry.bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        if max(width, height) <= threshold or count == 250:
            # either the polygon is smaller than the threshold, or the maximum
            # number of recursions has been reached
            return [geometry]
        if height >= width:
            # split left to right
            a = box(bounds[0], bounds[1], bounds[2], bounds[1]+height/2)
            b = box(bounds[0], bounds[1]+height/2, bounds[2], bounds[3])
        else:
            # split top to bottom
            a = box(bounds[0], bounds[1], bounds[0]+width/2, bounds[3])
            b = box(bounds[0]+width/2, bounds[1], bounds[2], bounds[3])
        result = []
        for d in (a, b,):
            c = geometry.intersection(d)
            if not isinstance(c, GeometryCollection):
                c = [c]
            for e in c:
                if isinstance(e, (Polygon, MultiPolygon)):
                    result.extend(katana(e, threshold, count+1))
        if count > 0:
            return result
        # convert multipart into singlepart
        final_result = []
        for g in result:
            if isinstance(g, MultiPolygon):
                final_result.extend(g)
            else:
                final_result.append(g)
        return final_result

    featureCollection = tzwhere.read_tzworld('tz_world.json')
    pgen = tzwhere._feature_collection_polygons(featureCollection)
    tzNamesToPolygons = collections.defaultdict(list)
    for tzname, poly in pgen:
        import pdb; pdb.set_trace()  # XXX BREAKPOINT
        shapelyPoly = Polygon(poly[0], poly[1])
        splitPolys = katana(shapelyPoly, 0.1)
        tzNamesToPolygons[tzname].extend(splitPolys)

    for tzname, polys in tzNamesToPolygons.items():
        # TODO save everything to int32
        tzNamesToPolygons[tzname] = \
            numpy.asarray(tzNamesToPolygons[tzname])

    with open('tz_world_polygons.pck', 'wb') as f:
        pickle.dump(tzNamesToPolygons, f)

    timezoneLongitudeShortcuts,\
        timezoneLatitudeShortcuts = _construct_shortcuts(
            tzNamesToPolygons, tzwhere.SHORTCUT_DEGREES_LONGITUDE,
            tzwhere.SHORTCUT_DEGREES_LATITUDE)

    with open('tz_world_shortcuts.pck', 'wb') as f:
        pickle.dump((timezoneLongitudeShortcuts, timezoneLatitudeShortcuts), f)

if __name__ == "__main__":
    main()
