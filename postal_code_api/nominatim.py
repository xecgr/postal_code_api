import requests
from postal_code_api.text import normalize_text
from django.conf import settings
import urllib
BASE_URL = 'http://open.mapquestapi.com/nominatim/v1/search.php?key={}&'.format(settings.NOMINATIM_KEY)

def get_location(location, province = None , country_code=settings.DEFAULT_COUNTRY_CODE):
    location = normalize_text(location)
    if province:
        location += u" {}".format(normalize_text(province.name))
    if country_code:
        location += u" {}".format(normalize_text(country_code))
    
    query_string = {
        'q'              : location,
        'format'         : 'json',
        'addressdetails' : 1,
    }
    url = BASE_URL + urllib.urlencode(query_string)
    req = requests.get(url)
    if 'exceeded' in req.text:
        print "Nominatim exceeded"
        raise Exception("Nominatim exceeded")
    results = [
        result
        for result in req.json()
        if result.get('address',{}).get('country_code','').lower() == country_code.lower()
    ] or [{}]
    return results[0]