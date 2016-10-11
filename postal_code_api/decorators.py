# -*- encoding: utf-8 -*-
from django.http import HttpResponse
import json

def json_response(endpoint):
    def _json_response(*args, **kwargs):
        return HttpResponse(json.dumps(endpoint(*args, **kwargs),sort_keys=True), content_type='application/json')
    return _json_response

