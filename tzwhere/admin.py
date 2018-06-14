from django.contrib.gis import admin
from django.contrib.gis.admin import OSMGeoAdmin

from geodjango_tzwhere.models import Timezone


class TimezoneAdmin(OSMGeoAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']
    ordering = ['name']


admin.site.register(Timezone, TimezoneAdmin)