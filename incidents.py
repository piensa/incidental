import click
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



@click.command()
@click.option('--count', default=1, help='Number of incidents.')
@click.option('--encoding', default='json', help='Use json encoding.')
@click.option('--broker', default=None, help='Kafka broker.')
@click.option('--verbose', default=True, help='Kafka broker.')
def incident(count, encoding, broker, verbose):
    # Create random incidents
    incident_list = random_incidents(count)

    if encoding == 'json':
        for incident_item in incident_list:
            incident_json = json.dumps(incident_item, sort_keys=True, default=str)
            if verbose:
                print(incident_json)
    elif encoding == 'avro':
        from fastavro.schema import load_schema
        from fastavro import writer

        schema = load_schema('incident.avsc')
        with open('incident.avro', 'wb') as out:
            writer(out, schema, incident_list, codec='snappy')


def serialize_ts(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    return long((dt - epoch).total_seconds() * 1000.)


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
        incident_date = fake.date_time_between(start_date="-15y", end_date="-5y", tzinfo=None)
	dispatched_delta = random.randint(5, 10)
	enroute_delta = random.randint(5, 60)
	arrived_delta = random.randint(120, 1200)
	available_delta = random.randint(60, 5000)
	station = stations[response_zone]
	unit = random.choice(station['units'])
	incident_type = random.choice(INCIDENT_TYPES.keys())
	subincident_type = random.choice(INCIDENT_TYPES[incident_type])

	dispatched_date = incident_date + datetime.timedelta(seconds=dispatched_delta)
	enroute_date = dispatched_date + datetime.timedelta(seconds=enroute_delta)
	arrived_date = enroute_date + datetime.timedelta(seconds=arrived_delta)
	available_date = arrived_date + datetime.timedelta(seconds=available_delta)

	incident_dict = dict(
	apparatus_car_id=str(unit['car_id']),
	apparatus_shift=unit['shift'],
	apparatus_unit_type=unit['unit_type'],
        apparatus_dispatched=serialize_ts(dispatched_date),
        apparatus_enroute=serialize_ts(enroute_date),
        apparatus_arrived=serialize_ts(arrived_date),
        apparatus_available=serialize_ts(available_date),
	address_line1=fake.address().split('\n')[0],
	address_latitude=sample[9] + random.uniform(-0.01, 0.01),
	address_longitude=sample[10] + random.uniform(-0.01, 0.01),
	address_state=state,
	address_postal_code=sample[1],
	description_comments=fake.text(),
	description_event_opened=serialize_ts(incident_date),
	description_event_closed=serialize_ts(available_date),
	description_first_unit_dispatched=serialize_ts(dispatched_date),
	description_first_unit_arrived=serialize_ts(arrived_date),
	description_first_unit_enroute=serialize_ts(enroute_date),
	description_type=incident_type,
	description_subtype=subincident_type,
	fire_dpt_name=station['name'],
	fire_dpt_shift=unit['shift'],
	fire_dpt_lat=station['lat'],
	fire_dpt_lon=station['lon'],
	fire_dpt_state=station['state'],
	)

        incident_list.append(incident_dict)

    return incident_list


if __name__=='__main__':
    incident()
