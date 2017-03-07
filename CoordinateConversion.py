# The speed can probably be improved by using a less accurate GeoJSON file if necessary!

import json
from shapely.geometry import Point, shape

# Load the GeoJSON data from the file
with open('GBR_GeoJSON.json') as data_file:
    UK_json = json.load(data_file)

# Function that returns region name based on input data
def get_location(longitude, latitude, json_file):
    point = Point(longitude, latitude)
    for record in json_file['features']:
        polygon = shape(record['geometry'])
        if polygon.contains(point):
            return record['properties']['NAME_2'] #Change to NAME_1 for the country
    return 'other'

# Plug your coordinates in here
# Bristol = 51.4545 North, 2.5879 West
long = -2.5879
lat = 51.4545

location = get_location(long,lat,UK_json)
print(location)