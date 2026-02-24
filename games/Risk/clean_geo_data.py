import geopandas as gpd
from shapely.geometry import mapping
import numpy as np

geo_data = gpd.read_file("Risk/data/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp")

geo_data.head(3)

columns = [
    "ADMIN",
    "CONTINENT",
    "geometry"
]

geo_data[columns].head(3)

geo_data[geo_data.CONTINENT == "Europe"].ADMIN.unique()

remove_list = [
    'Vatican',
    'Jersey', 'Guernsey', 'Isle of Man',
    'San Marino',
    'Russia',
    'Monaco',
    'Liechtenstein',
    'Aland',
    'Faroe Islands',
    'Andorra',
    'Malta'
]

country_coords = {}
for idx, row in geo_data[(geo_data.CONTINENT == "Europe") & (~geo_data.ADMIN.isin(remove_list))].iterrows():
    geojson_obj = mapping(row["geometry"])
    geo_coords = geojson_obj["coordinates"]
    idx = np.argmax([len(coords[0]) for coords in geo_coords])
    country_coords[row["ADMIN"]] = geo_coords[idx]
countries = {}
for country_name, country_coord in country_coords.items():
    while len(country_coord) < 5:
        country_coord = country_coord[0]
    countries[country_name] = country_coord
import json

with open('Risk/data/country_coords.json', 'w') as f:
    json.dump(countries, f)