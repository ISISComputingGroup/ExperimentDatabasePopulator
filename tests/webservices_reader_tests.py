import unittest
from exp_db_populator.database_model import Experiment
from tests.webservices_test_data import *
from exp_db_populator.data_types import UserData, ExperimentTeamData
from exp_db_populator.webservices_reader import LOCAL_ORG, LOCAL_ROLE, reformat_data, \
    get_start_and_end, get_experimenters, get_credentials
from datetime import datetime, timedelta
from mock import patch, MagicMock


class WebServicesReaderTests(unittest.TestCase):
    def test_WHEN_get_start_and_end_date_of_100_THEN_time_difference_of_200(self):
        start, end = get_start_and_end(datetime.now(), 100)
        self.assertEqual(timedelta(days=200), end-start)

    def test_WHEN_get_start_and_end_date_of_100_THEN_stat_before_end(self):
        start, end = get_start_and_end(datetime.now(), 100)
        self.assertTrue(start < end)

    def test_GIVEN_experimenters_WHEN_get_experimenters_THEN_get_experimenters(self):
        team = MagicMock()
        team.experimenters = ["TEST"]
        self.assertEqual(["TEST"], get_experimenters(team))

    def test_GIVEN_no_experimenters_WHEN_get_experimenters_THEN_empty_list(self):
        team = MagicMock(spec=['NOT_EXPERIMENTEERS'])
        self.assertEqual([], get_experimenters(team))

    def test_GIVEN_no_data_set_WHEN_data_formatted_THEN_no_data_set(self):
        experiments, experiment_teams = reformat_data([], [], [])

        self.assertEqual(experiments, [])
        self.assertEqual(experiment_teams, [])

    def test_GIVEN_dates_WHEN_data_formatted_THEN_experiment_list_populated(self):
        experiments, experiment_teams = reformat_data([], TEST_DATES, [])

        self.assertEqual(len(experiments), 1)
        exp_entry = experiments[0]
        self.assertEqual(exp_entry[Experiment.experimentid], TEST_RBNUMBER)
        self.assertEqual(exp_entry[Experiment.startdate], TEST_DATE)
        self.assertEqual(exp_entry[Experiment.duration], TEST_TIMEALLOCATED)

    def test_GIVEN_multiple_dates_WHEN_data_formatted_THEN_experiment_list_contains_both(self):
        rb, date, duration = 2000, datetime(1992, 2, 7), 10
        dates = TEST_DATES + [create_date_data(rb, date, duration)]
        experiments, experiment_teams = reformat_data([], dates, [])

        self.assertEqual(len(experiments), 2)
        for entry in experiments:
            if entry[Experiment.experimentid] == TEST_RBNUMBER:
                self.assertEqual(entry[Experiment.startdate], TEST_DATE)
                self.assertEqual(entry[Experiment.duration], TEST_TIMEALLOCATED)
            else:
                self.assertEqual(entry[Experiment.experimentid], rb)
                self.assertEqual(entry[Experiment.startdate], date)
                self.assertEqual(entry[Experiment.duration], duration)

    def test_GIVEN_local_contacts_and_no_corresponding_date_WHEN_data_formatted_THEN_exception_thrown(self):
        self.assertRaises(KeyError, reformat_data, [], [], TEST_CONTACTS)

    def test_GIVEN_local_contacts_and_corresponding_date_WHEN_data_formatted_THEN_experiment_teams_populated(self):
        experiments, experiment_teams = reformat_data([], TEST_DATES, TEST_CONTACTS)

        expected_user = UserData(TEST_CONTACT_NAME, LOCAL_ORG)
        expected_user_data = ExperimentTeamData(expected_user, LOCAL_ROLE, TEST_RBNUMBER, TEST_DATE)

        self.assertEqual(len(experiment_teams), 1)
        self.assertTrue(expected_user_data == experiment_teams[0])

    def test_GIVEN_user_and_no_corresponding_date_WHEN_data_formatted_THEN_exception_thrown(self):
        team = get_test_experiment_team([TEST_USER_1])
        self.assertRaises(KeyError, reformat_data, [team], [], [])

    def test_GIVEN_user_and_corresponding_date_WHEN_data_formatted_THEN_experiment_teams_populated(self):
        team = get_test_experiment_team([TEST_USER_1])
        experiments, experiment_teams = reformat_data([team], TEST_DATES, [])

        expected_user = UserData(TEST_USER_1_NAME, TEST_USER_1_ORG)
        expected_user_data = ExperimentTeamData(expected_user, TEST_USER_1_ROLE, TEST_RBNUMBER, TEST_DATE)

        self.assertEqual(len(experiment_teams), 1)
        self.assertTrue(expected_user_data == experiment_teams[0])

    def test_GIVEN_user_and_pi_and_corresponding_date_WHEN_data_formatted_THEN_experiment_teams_populated(self):
        team = get_test_experiment_team([TEST_USER_1, TEST_USER_PI])
        experiments, experiment_teams = reformat_data([team], TEST_DATES, [])

        expected_user_1 = UserData(TEST_PI_NAME, TEST_PI_ORG)
        expected_user_data_1 = ExperimentTeamData(expected_user_1, TEST_PI_ROLE, TEST_RBNUMBER, TEST_DATE)

        expected_user_2 = UserData(TEST_USER_1_NAME, TEST_USER_1_ORG)
        expected_user_data_2 = ExperimentTeamData(expected_user_2, TEST_USER_1_ROLE, TEST_RBNUMBER, TEST_DATE)

        expected_user_data = [expected_user_data_2, expected_user_data_1]

        self.assertEqual(len(experiment_teams), 2)
        self.assertTrue(expected_user_data == experiment_teams)
