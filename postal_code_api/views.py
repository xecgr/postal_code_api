from django.shortcuts import render
from postal_code_api.decorators import json_response
from postal_code_api  import models
from postal_code_api.text import normalize_text
import json, re, string

@json_response
def find_location(request,country_code=None,postal_code=None):
    result = {}
    if country_code:
        country = models.Country.objects.filter(country_code=country_code.upper())
        if country.exists():
            country     = country[0]
            if postal_code:
                postal_code  = postal_code.strip()
                _postal_code = models.Postal_Code.objects.filter(postal_code = postal_code)
                if _postal_code.exists():
                    location = _postal_code[0].location
                    result = prepare_result(location)
                else:
                    result['error'] = 'No mathes for postal code: {}'.format(postal_code)
            else:
                q          = request.GET.get('q','').strip()
                if q:
                    norm_query = normalize_text(q)
                    synonim    = models.Location_Synonim.objects.filter(norm_name = norm_query)
                    location   = None
                    if synonim.exists():
                        location = synonim[0].location
                        result = prepare_result(location)
                    else:
                        #maybe it's a qualified string: "city, country" ("Madrid, spain")
                        pattern     = r"[{}]".format(string.punctuation)
                        query_parts = [_q.strip() for _q in re.split(pattern,q) if _q.strip()]
                        if len(query_parts)>1:
                            for _q in query_parts:
                                norm_query = normalize_text(_q)
                                synonim    = models.Location_Synonim.objects.filter(norm_name = norm_query)
                                if synonim:
                                    location = synonim[0].location
                                    result = prepare_result(location)
                                    break
                        #finally, try a nominatim search
                        if not location:
                            location = models.Location.get_unknown_location(q,country=country)
                            if location:
                                result = prepare_result(location)
                            else:
                                result['error'] = 'No matches for query: {}'.format(q)
                else:
                    result['error'] = 'Empty query'
        else:
            result['error'] = 'Unknown country code: {}'.format(country_code.upper())
    else:
        result['error'] = 'No country code passed'
    return result


def prepare_result(location):
    result = {}
    if location.json_data:
        result = json.loads(location.json_data)
    result['country'] = location.country.name
    result['region']  = location.region.name
    result['region_code']  = location.region.region_code
    result['name']  = location.name
    result['synonims']  = [s.synonim for s in models.Location_Synonim.objects.filter(location = location).order_by('synonim')]
    result['postal_codes']  = [pc.postal_code for pc in models.Postal_Code.objects.filter(location = location).order_by('postal_code')]
    
    return result
    