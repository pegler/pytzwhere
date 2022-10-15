#!/usr/bin/env python

'''tzwhere.py - time zone computation from latitude/longitude.
'''
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from tzwhere.models import Timezone

try:
    import ujson as json # loads 2 seconds faster than normal json
except:
    try:
        import json
    except ImportError:
        import simplejson as json
import os

# for navigation and pulling values/files
this_dir, this_filename = os.path.split(__file__)
BASE_DIR = os.path.dirname(this_dir)

class tzwhere(object):
    DEFAULT_POLYGONS = os.path.join(os.path.dirname(__file__),
                                    'tz_world.json.gz')

    def __init__(self, forceTZ=False):
        self.forceTZ = forceTZ

    def tzNameAt(self, latitude, longitude, forceTZ=False):
        '''
        Lookup the timezone name for a given latitude and longitude.
        @latitude: latitude
        @longitude: longitude
        @forceTZ: If forceTZ is true and you can't find a valid timezone return
        the closest timezone you can find instead.
        '''
        point = Point(longitude, latitude, srid=4326)
        zones = Timezone.objects.filter(polygon__contains=point)
        if len(zones):
            return zones[0].name
        elif forceTZ:
            # Return timezone with nearest polygon
            # Limit search to within 2 degrees, otherwise the query takes too long (DWithin makes use of index)
            matches = Timezone.objects\
                .filter(polygon__dwithin=(point, 2))\
                .annotate(distance=Distance('polygon', point))\
                .order_by('distance')
            if len(matches):
                return matches[0].name
            return None
