#wget http://download.geonames.org/export/dump/cities15000.zip
#unzip cities15000.zip 

import csv
country_cities = {}
COUNTRY_IDX    = 8
CITY_IDX       = 1
SINONYMS_IDX   = 3
SINONYMS_COUNT = 5
POPULATION_IDX = 14
CITY_NUM = 5

country_codes = [
    "ES"
]
city_country = {}

with open('cities15000.txt', 'rb') as csvfile, open('ES.cities15000.txt', 'wb') as csvfile_out:
    reader = csv.reader(csvfile, delimiter='\t')
    writer = csv.writer(csvfile_out, delimiter='\t')
    for row in reader:
        if row[COUNTRY_IDX] in country_codes:
            writer.writerow(row)
