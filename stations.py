import random
import pandas as pd
import numpy as np
import faker
import datetime
import pprint
import json


# Column definition from GeoNames US txt dump.
dtypes_dict = {
    0: str, # country code
    1: str,  # postal code
    2: str,  # place name
    3: str,  # state name
    4: str,  # state code
    5: str,  # county name
    6: str,  # county code
    7: str,  # city name
    8: str,  # city code
    9: float, # latitude
    10: float, # longitude
    11: str, # accuracy
}
# Load GeoNames onto a pandas data frame
data = pd.read_csv("US.txt", sep="\t", header = None, dtype=dtypes_dict)
fake = faker.Faker()

UNIT_TYPES = ('Safety Officer', 'Truck/Aerial', 'Mobile Command Post', 'Engine', 'Rescue Unit', 'Chief Officer', 'Brush Truck', 'Light and Air Unit', 'Hazmat Unit', 'Support Unit')
SHIFT_TYPES = ('A', 'B', 'C')

STATIONS={}

# We'll add one fire station per zip code and between 2 and 10 fire trucks to each station.
for idx in data.index:

    item = data.iloc[idx]
    units_number=random.randint(2, 10)

    units = []

    for unit_id in xrange(units_number):
        unit_dict = dict(
        car_id= int(item[1])*1000 + unit_id,
        shift=random.choice(SHIFT_TYPES),
        unit_type=random.choice(UNIT_TYPES),
        )
        units.append(unit_dict)

    station_item = dict(
    code=item[1],
    name='%s Fire Station' % fake.name(),
    lat=item[9],
    lon=item[10],
    state=item[4],
    units=units,
    )

    STATIONS[item[1]] = station_item

with open('stations.json', 'w') as outfile:
    json.dump(STATIONS, outfile, sort_keys=True, indent=2)
