from __future__ import unicode_literals
from django.db import models
from postal_code_api.nominatim import get_location
from postal_code_api.text import normalize_text
from django.conf import settings

class Country(models.Model):
    country_code = models.CharField(max_length=16)
    name         = models.CharField(max_length=32)
    

class Region(models.Model):
    country      = models.ForeignKey(Country, on_delete=models.CASCADE)
    region_code  = models.CharField(max_length=16)
    name         = models.CharField(max_length=32)


class Province(models.Model):
    country       = models.ForeignKey(Country, on_delete=models.CASCADE)
    region        = models.ForeignKey(Region, on_delete=models.CASCADE)
    zip_code      = models.CharField(max_length=16,null=True)
    official_code = models.CharField(max_length=16,null=True)
    name          = models.CharField(max_length=32)


class Location(models.Model):
    country   = models.ForeignKey(Country, on_delete=models.CASCADE)
    region    = models.ForeignKey(Region, on_delete=models.CASCADE)
    province  = models.ForeignKey(Province, on_delete=models.CASCADE)
    name      = models.CharField(max_length=256)
    json_data = models.TextField(null=True)
    
    @classmethod
    def get_unknown_location(cls,name,country=None):
        country_code = None
        if country:
            country_code = country.country_code
        location = get_location(name,country_code=country_code)
        l        = None
        if location:
            nominatim_name = location.get('display_name','').split(",")[0].strip() or name.capitalize()
            json_data      = {
                k:v
                for k,v in location.iteritems()
                if k in ['lat','lon','boundingbox']
            }
            kwargs = {'name':nominatim_name}
            if country:
                kwargs['country'] = country
            l = Location.objects.filter(**kwargs)
            if l.exists():
                l = l[0]
                _ = Location_Synonim.objects.get_or_create(
                    location  = l,
                    synonim   = name.capitalize(),
                    norm_name = normalize_text(name)
                )
        return l

class Location_Synonim(models.Model):
    location  = models.ForeignKey(Location, on_delete=models.CASCADE)
    synonim   = models.CharField(max_length=256)
    norm_name = models.CharField(max_length=256,null=True)

class Postal_Code(models.Model):
    location    = models.ForeignKey(Location, on_delete=models.CASCADE)
    postal_code = models.CharField(max_length=16)
