# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-06 16:01
from __future__ import unicode_literals
from django.db import migrations
from django.conf import settings
import glob,os,json,codecs,re
from postal_code_api.nominatim import get_location
from postal_code_api  import models
from postal_code_api.text import normalize_text

DATA_SEPARATOR = u':'
ARTICLES_LENGTH = 3

def run():
    name__postal_codes = {}
    synonims           = {}
    for file in glob.glob(os.path.join(settings.BASE_DIR,'raw_data/*xcodpos.txt')):
        with codecs.open(file, encoding='ISO8859') as f_in:
            count = 0
            for line in f_in:
                postal_code, text = line.split(DATA_SEPARATOR)
                #32152:ALEMPARTE (PEROXA, A)
                #32150:CONCHOUSO, O (GUERAL-PEROXA, A)
                #easy match
                #07141:SA CABANA
                #big city match, crawl codciu
                #08000:BARCELONA (VER CALLEJERO)
                #multipart match
                #destination description, skip
                #07740:S'ARENAL D'EN CASTELL (MENORCA), Urbanitzacio
                #07769:DELFINES, LOS, Urbanizacion
                #07711:BINIBECA, DE, Platja
                #mutlipart with articles
                #07700:MESQUIDA (SA), Platja
                #07639:RAPITA (SA)
                #07711:UESTRA, S' (SANT LLUIS), Urbanitzacio
                #07711:ULLASTRAR, L'
                #too accurated
                #07800:EIVISSA-SAN JUAN (CARRETERA), HASTA KM.1,900
                #multiname
                #07190:PORT DES CANONGE/PORT DEL CANONGE
                #01439:GUILLARTE / GIBILLOARRATE
                names      = [] 
                if '(VER CALLEJERO)' in text:
                    #big city, we'll parse them later
                    continue
                m = re.match(u"^[\w,\s']+",text)
                if m:
                    text = m.group()
                for name in text.split(u"/"):
                    name_parts = name.split(u",")
                    if len(name_parts) == 2 or len(name_parts) == 3:
                        if len(name_parts) == 3:
                            name_parts = name_parts[:2] #skip 
                        
                        multiparts = name_parts[0].split(u"(")
                        if len(multiparts) == 2 and len(multiparts[1].replace(u")",u""))<=ARTICLES_LENGTH :
                            names.append(
                                multiparts[1].replace(u")",u"").strip() + u" " + multiparts[0].strip()
                            )
                        elif len(name_parts[1].strip())<=ARTICLES_LENGTH:
                            names.append(
                                name_parts[1].replace(u")",u"").strip() + u" " + name_parts[0].strip()
                            )
                    names.append(
                        name_parts[0].split(u"(")[0].strip()
                    )
                curr_name = names[0].strip()
                if curr_name and curr_name not in ["A","LA","LOS","EL","O"]:
                    name__postal_codes.setdefault(curr_name,[]).append(postal_code.strip())
                    for synonim in names[1:]:
                        synonim= synonim.strip()
                        if synonim.strip() not in synonims.get(curr_name,[]):
                            synonims.setdefault(curr_name,[]).append(synonim.strip())
    """
    file_path = 'raw_data/name__postal_codes.json'
    json.dump(name__postal_codes, open(os.path.join(settings.BASE_DIR,file_path), "wb" ), sort_keys=True, indent=4, ensure_ascii=True)
    file_path = 'raw_data/synonims.json'
    json.dump(synonims, open(os.path.join(settings.BASE_DIR,file_path), "wb" ), sort_keys=True, indent=4, ensure_ascii=True)
    
    with codecs.open(os.path.join(settings.BASE_DIR,'raw_data/codciu.txt'), encoding='ISO8859') as f_in:
        city__postal_codes = {}
        city_synonims = {}
        
        for line in f_in:
            big_city_prefix = line[:3]
            big_city_name   = line[3:]
            if not big_city_prefix.endswith('x'):
                postal_codes = set()
                with codecs.open(os.path.join(settings.BASE_DIR,'raw_data/{}codpos.txt'.format(big_city_prefix)), encoding='ISO8859') as big_city_in:
                    for street in big_city_in:
                        postal_code,text = street.split(":")
                        postal_codes.add(postal_code.strip())
                big_city_names = big_city_name.split("/")
                big_city_name  = big_city_names[0].strip()
                city__postal_codes[big_city_name] = list(postal_codes)
                for synonim in big_city_names[1:]:
                    city_synonims.setdefault(big_city_name,[]).append(synonim.strip())
        file_path = 'raw_data/city__postal_codes.json'
        json.dump(city__postal_codes, open(os.path.join(settings.BASE_DIR,file_path), "wb" ), sort_keys=True, indent=4, ensure_ascii=True)
        file_path = 'raw_data/city_synonims.json'
        json.dump(city_synonims, open(os.path.join(settings.BASE_DIR,file_path), "wb" ), sort_keys=True, indent=4, ensure_ascii=True)
    """
    province_cache = {}
    location_dicts = [
        (name__postal_codes,synonims),
        #(city__postal_codes,city_synonims)
    ]
    fixes = []
    for _name__postal_codes, _synonims in location_dicts:
        for name, postal_codes in _name__postal_codes.iteritems():
            if models.Location_Synonim.objects.filter(norm_name = normalize_text(name)).exists():
                #already loaded location
                print "already loaded location: "+ normalize_text(name)
                continue
            province_prefix = postal_codes[0][:2]
            province = province_cache.get(province_prefix,models.Province.objects.filter(zip_code=province_prefix))
            if province.exists():
                province = province[0]
            else:
                print "NOT EXIST PROVINCE: "+province_prefix
                fixes.append(name)
                continue
                province = None
            location = get_location(name,province=province) or {}
            nominatim_name = location.get('display_name','').split(",")[0].strip() or name.capitalize()
            json_data      = {
                k:v
                for k,v in location.iteritems()
                if k in ['lat','lon','boundingbox']
            }
            l,_ = models.Location.objects.get_or_create(
                name        = nominatim_name,
                province    = province if province else None,
                region      = province.region if province else None,
                country     = province.country if province else None,
                json_data   = json.dumps(json_data) if json_data else None
            )
            for pc in postal_codes:
                models.Postal_Code.objects.get_or_create(
                    location    = l,
                    postal_code = pc
                )
            for synonim in _synonims.get(name,[]) + [name]:
                _ = models.Location_Synonim.objects.get_or_create(
                    location  = l,
                    synonim   = synonim.capitalize(),
                    norm_name = normalize_text(synonim)
                )
    file_path = 'raw_data/fixes.json'
    json.dump(fixes, open(os.path.join(settings.BASE_DIR,file_path), "wb" ), sort_keys=True, indent=4, ensure_ascii=True)
    