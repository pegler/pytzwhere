from django.contrib.gis.db import models
from django.contrib.gis.db.models import MultiPolygonField


class Timezone(models.Model):
    name = models.CharField(max_length=200)
    polygon = MultiPolygonField(srid=4326)