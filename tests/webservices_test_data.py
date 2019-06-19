from datetime import datetime
from mock import MagicMock, PropertyMock
TEST_INSTRUMENT = 'test_instrument'
TEST_OTHER_INSTRUMENT = "test_other_instrument"
TEST_RBNUMBER = '10000'
TEST_TIMEALLOCATED = 7
TEST_DATE = datetime(2018, 1, 1)

TEST_CONTACT_NAME = 'Dr Ron Smith'

TEST_USER_1_NAME = 'Dr Bill Smith'
TEST_USER_1_ORG = 'University'
TEST_USER_1_ROLE = 'User'

TEST_PI_NAME = 'Dr John White'
TEST_PI_ORG = 'STFC'
TEST_PI_ROLE = 'PI'

TEST_USER_1 = {'name': TEST_USER_1_NAME, 'organisation': TEST_USER_1_ORG, 'role': TEST_USER_1_ROLE}
TEST_USER_PI = {'name': TEST_PI_NAME, 'organisation': TEST_PI_ORG, 'role': TEST_PI_ROLE}

def create_date_data(rb, start, duration):
    return {'instrument': TEST_INSTRUMENT, 'part': 6, 'rbNumber': rb, 'scheduledDate': start, 'timeAllocated': duration}

TEST_DATES = [create_date_data(TEST_RBNUMBER, TEST_DATE, TEST_TIMEALLOCATED)]

TEST_CONTACTS = [{'instrument': TEST_INSTRUMENT, 'name': TEST_CONTACT_NAME,
                  'rbNumber': TEST_RBNUMBER}]


def get_test_experiment_team(experimenters):
    team_dict = {'experimenters': experimenters, 'instrument': TEST_INSTRUMENT,
                 'part': 6, 'rbNumber': TEST_RBNUMBER}

    team = MagicMock()
    team.experimenters = experimenters
    team.__getitem__.side_effect = team_dict.__getitem__
    return team