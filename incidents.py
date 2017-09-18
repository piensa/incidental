
import click
import fastavro as avro
import random
import pandas as pd
import faker
import datetime
import pprint
import json


# Column definition from GeoNames US txt dump.
dtypes_dict = {
    0: str,  # country code
    1: str,  # postal code
    2: str,  # place name
    3: str,  # state name
    4: str,  # state code
    5: str,  # county name
    6: str,  # county code
    7: str,  # city name
    8: str,  # city code
    9: float,  # latitude
    10: float,  # longitude
    11: str,  # accuracy
}

# Taken from
# http://www.nfpa.org/~/media/files/news-and-research/fire-statistics/fire-service/osnfirsincidenttype.pdf?la=en
INCIDENT_TYPES = {
    'Fire': (
    'Structure Fire',
    'Fire in mobile property used as fixed structure',
    'Mobile property (vehicle) fire',
    'Natural vegetation fire',
    'Outside rubbish fire',
    'Special outside fire',
    'Cultivated vegetation, crop fire',
    'Fire, other',
    ),
    'Overpressure rupture, explosion, overheat': (
    'Overpressure rupture from steam',
    'Overpressure rupture from air or gas',
    'Overpressure rupture from chemical reaction',
    'Explosion',
    'Excessive heat, scorch burns with no ignition',
    'Overpressure rupture, explosion, overheat, other',
    ),
    'Rescue & Emergency Medical Service': (
    'Medical Assist',
    'EMS Incident',
    'Lock-in',
    'Search for lost person',
    'Extrication, rescue',
    'Water & Ice related rescue',
    'Electrical Rescue',
    'Rescue or EMS Standby',
    'Rescue, EMS, Other',
    ),
    'Hazardous conditions': (
    'Combustible / Flammable spills & leaks',
    'Chemical release, reaction or toxic condition',
    'Radioactive condition',
    'Electrical wiring / equipment problem',
    'Biological Hazard',
    'Accident, potential accident',
    'Explosive, bomb removal',
    'Attempted burning, illegal action',
    'Hazardous condition, other',
    ),
    'Service calls': (
    'Person in distress',
    'Water problem',
    'Smoke, odor problem',
    'Animal problem or rescue',
    'Public service assistance',
    'Unathorized burning',
    'Cover assignement, standby at fire station, move-up',
    'Service call, other',
    ),
    'Good intent': (
    'Dispatched & canceled en route',
    'Wrong location, no emergency found',
    'Controlled burning',
    'Vicinity alarm',
    'Steam, other gas mistaken for smoke',
    'EMS call where other party had been transported',
    'HazMat release investigation with no HazMat found',
    'Good intent call, other',
    ),
    'False alarm': (
    'Malicious, mischievous, false alarm',
    'Bomb scare (no bomb)',
    'System or detector malfunction',
    'Unintentional system or detector operation (no fire)',
    'Biological hazard, malicious false report',
    'False alarm and false call, other',
    ),
    'Weather / natural disaster': (
    'Severe weather & natural disaster',
    'Severe weather & natural disaster, other',
    ),
    'Special incident type': (
    'Citizen complaint',
    'Special incident type, other',
    ),
}

AVRO_SCHEMA="""
[
  {
    "fields": [
      {
        "name": "address_line",
        "type": "string"
      },
      {
        "name": "latitude",
        "type": "float"
      },
      {
        "name": "longitude",
        "type": "float"
      },
      {
        "name": "postal_code",
        "type": "string"
      },
      {
        "name": "state",
        "type": "string"
      }
    ],
    "name": "address",
    "type": "record"
  },
  {
    "fields": [
      {
        "name": "arrived",
        "type": "timestamp-millis"
      },
      {
        "name": "available",
        "type": "timestamp-millis"
      },
      {
        "name": "dispatched",
        "type": "timestamp-millis"
      },
      {
        "name": "enroute",
        "type": "timestamp-millis"
      }
    ],
    "name": "unit_status",
    "type": "record"
  },
  {
    "fields": [
      {
        "name": "card_id",
        "type": "string"
      },
      {
        "name": "shift",
        "type": "string"
      },
      {
        "name": "unit_type",
        "type": "string"
      },
      {
        "name": "unit_status",
        "type": "unit_status"
      }
    ],
    "name": "apparatus",
    "type": "record"
  },
  {
    "fields": [
      {
        "name": "comments",
        "type": "string"
      },
      {
        "name": "event_closed",
        "type": "timestamp-millis"
      },
      {
        "name": "event_opened",
        "type": "timestamp-millis"
      },
      {
        "name": "first_unit_arrived",
        "type": "timestamp-millis"
      },
      {
        "name": "first_unit_dispatched",
        "type": "timestamp-millis"
      },
      {
        "name": "first_unit_enroute",
        "type": "timestamp-millis"
      },
      {
        "name": "subtype",
        "type": "string"
      },
      {
        "name": "type",
        "type": "string"
      }
    ],
    "name": "description",
    "type": "record"
  },
  {
    "fields": [
      {
        "name": "lat",
        "type": "float"
      },
      {
        "name": "lon",
        "type": "float"
      },
      {
        "name": "name",
        "type": "string"
      },
      {
        "name": "shift",
        "type": "string"
      },
      {
        "name": "state",
        "type": "string"
      }
    ],
    "name": "fire_department",
    "type": "record"
  },
  {
    "fields": [
      {
        "name": "address",
        "type": "address"
      },
      {
        "name": "apparatus",
        "type": "apparatus"
      },
      {
        "name": "description",
        "type": "description"
      },
      {
        "name": "fire_department",
        "type": "fire_department"
      }
    ],
    "name": "incident",
    "type": "record"
  }
]
"""

@click.command()
@click.option('--count', default=1, help='Number of incidents.')
@click.option('--avro', default=False, help='Use avro encoding.')
@click.option('--broker', default=None, help='Kafka broker.')
@click.option('--verbose', default=True, help='Kafka broker.')
def incident(count, avro, broker, verbose):
    # Create random incidents
    incident_list = random_incidents(count)

    # If avro encoding was chosen, it does it
    if not avro and verbose:
        incident_json = json.dumps(incident_list, indent=2, sort_keys=True, default=str)
        print(incident_json)

    # If avro encoding was chosen.
    if avro:
       pass

       # If a kafka broker is defined, it is sent there.
       if broker:
           pass


def random_incidents(count):
    # Load GeoNames onto a pandas data frame
    data = pd.read_csv("US.txt", sep="\t", header=None, dtype=dtypes_dict)

    stations = None
    with open('stations.json') as stations_file:
        stations = json.load(stations_file)

    incident_list = []

    for i in xrange(count):
	# Take just one random item.
	index = random.randint(0, len(data))
	sample = data.iloc[index]

	# Create fake address and name
	fake = faker.Faker()
	name = fake.name()

	# Fake response zone with the zipcode.
	response_zone = sample[1]
	state = sample[4]

	address_dict = dict(
	address_line1=fake.address().split('\n')[0],
	latitude=sample[9] + random.uniform(-0.01, 0.01),
	longitude=sample[10] + random.uniform(-0.01, 0.01),
	state=state,
	postal_code=sample[1],
	)

	incident_date = fake.date_time_between(start_date="-15y", end_date="-5y", tzinfo=None)
	dispatched_delta = random.randint(5, 10)
	enroute_delta = random.randint(5, 60)
	arrived_delta = random.randint(120, 1200)
	available_delta = random.randint(60, 5000)

	dispatched_date = incident_date + datetime.timedelta(seconds=dispatched_delta)
	enroute_date = dispatched_date + datetime.timedelta(seconds=enroute_delta)
	arrived_date = enroute_date + datetime.timedelta(seconds=arrived_delta)
	available_date = arrived_date + datetime.timedelta(seconds=available_delta)

	unit_status_dict = dict(
	dispatched=dispatched_date,
	enroute=enroute_date,
	arrived=arrived_date,
	available=available_date,
	)

	station = stations[response_zone]

	unit = random.choice(station['units'])

	apparatus_dict = dict(
	car_id=unit['car_id'],
	shift=unit['shift'],
	unit_type=unit['unit_type'],
	unit_status=unit_status_dict,
	)

	incident_type = random.choice(INCIDENT_TYPES.keys())
	subincident_type = random.choice(INCIDENT_TYPES[incident_type])

	description_dict = dict(
	comments=fake.text(),
	event_opened=incident_date,
	event_closed=available_date,
	first_unit_dispatched=dispatched_date,
	first_unit_arrived=arrived_date,
	first_unit_enroute=enroute_date,
	type=incident_type,
	subtype=subincident_type,
	)

	station_dict = dict(
	name=station['name'],
	shift=unit['shift'],
	lat=station['lat'],
	lon=station['lon'],
	state=station['state'],
	)

	incident_dict = {
	"address": address_dict,
	"apparatus": apparatus_dict,
	"description": description_dict,
	# Station is synonym with fire department in this dataset.
	"fire_department": station_dict,
	"version": "1.0.29",
	}

        incident_list.append(incident_dict)

    return incident_list


if __name__=='__main__':
    incident()
