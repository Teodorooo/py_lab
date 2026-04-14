import geopandas as gpd
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

geo_data = gpd.read_file(os.path.join(BASE_DIR, "data/ne_50m_admin_0_countries/ne_50m_admin_0_countries.shp"))

columns = [
    "ADMIN",
    "CONTINENT",
    "geometry"
]

# Microstates, small islands, and dependent territories to exclude
remove_list = [
    # European microstates
    'Vatican',
    'San Marino',
    'Monaco',
    'Liechtenstein',
    'Andorra',
    # Small European islands/territories
    'Jersey', 'Guernsey', 'Isle of Man',
    'Aland',
    'Faroe Islands',
    'Malta',
    'Svalbard',
    # Pacific microstates and small island nations
    'Nauru',
    'Tuvalu',
    'Palau',
    'Marshall Islands',
    'Micronesia',
    'Federated States of Micronesia',
    'Kiribati',
    'Tonga',
    'Samoa',
    'American Samoa',
    'Cook Islands',
    'Niue',
    'Tokelau',
    'Wallis and Futuna',
    'French Polynesia',
    'New Caledonia',
    'Pitcairn Islands',
    'Norfolk Island',
    'Cocos (Keeling) Islands',
    'Christmas Island',
    'Heard Island and McDonald Islands',
    # Caribbean small island nations and territories
    'Saint Kitts and Nevis',
    'Antigua and Barbuda',
    'Dominica',
    'Saint Lucia',
    'Saint Vincent and the Grenadines',
    'Grenada',
    'Barbados',
    'Aruba',
    'Curacao',
    'Sint Maarten',
    'Saint Martin',
    'Saint Barthelemy',
    'Martinique',
    'Guadeloupe',
    'Puerto Rico',
    'United States Virgin Islands',
    'British Virgin Islands',
    'Turks and Caicos Islands',
    'Cayman Islands',
    'Montserrat',
    'Anguilla',
    # Small African and Indian Ocean island nations
    'Comoros',
    'Sao Tome and Principe',
    'Cape Verde',
    'Seychelles',
    'Mauritius',
    'Maldives',
    'Reunion',
    'Mayotte',
    # Other remote territories
    'Saint Pierre and Miquelon',
    'Falkland Islands',
    'South Georgia and the South Sandwich Islands',
    'British Indian Ocean Territory',
    'Bouvet Island',
    'French Southern and Antarctic Lands',
    # Special administrative regions
    'Hong Kong',
    'Macau',
    # Disputed/unrecognized territories
    'Western Sahara',
    'Somaliland',
]

countries = {}
for idx, row in geo_data[~geo_data.ADMIN.isin(remove_list)].iterrows():
    geom = row["geometry"]
    
    # Extract exterior coordinates directly from the largest polygon
    if geom.geom_type == 'Polygon':
        poly = geom
    elif geom.geom_type == 'MultiPolygon':
        # Get the largest polygon by area
        poly = max(geom.geoms, key=lambda p: p.area)
    else:
        continue
    
    # Simplify geometry with balanced tolerance (0.3 degrees)
    # Good balance between detail and performance for pole of inaccessibility
    simplified = poly.simplify(0.2, preserve_topology=True)
    coords = list(simplified.exterior.coords)
    
    # Convert coords to [lon, lat] format
    countries[row["ADMIN"]] = [[lon, lat] for lon, lat in coords]

with open(os.path.join(BASE_DIR, 'data/country_coords.json'), 'w') as f:
    json.dump(countries, f)
