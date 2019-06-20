import unittest
from exp_db_populator.database_model import Experiment
from tests.webservices_test_data import *
from exp_db_populator.data_types import UserData, ExperimentTeamData
from exp_db_populator.webservices_reader import LOCAL_ORG, LOCAL_ROLE, reformat_data, \
    get_start_and_end, get_experimenters, create_exp_team
from datetime import datetime, timedelta
from mock import MagicMock


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
        experiments, experiment_teams = reformat_data([])

        self.assertEqual(experiments, [])
        self.assertEqual(experiment_teams, [])

    def test_GIVEN_data_WHEN_data_formatted_THEN_experiment_list_populated(self):
        experiments, experiment_teams = reformat_data(TEST_DATA)

        self.assertEqual(len(experiments), 1)
        exp_entry = experiments[0]
        self.assertEqual(exp_entry[Experiment.experimentid], TEST_RBNUMBER)
        self.assertEqual(exp_entry[Experiment.startdate], TEST_DATE)
        self.assertEqual(exp_entry[Experiment.duration], TEST_TIMEALLOCATED)

    def test_GIVEN_rb_with_multiple_start_dates_WHEN_data_formatted_THEN_two_experiments_added(self):
        data = TEST_DATA + [create_data(TEST_RBNUMBER, datetime.now(), 3)]
        experiments, experiment_teams = reformat_data(data)

        self.assertEqual(len(experiments), 2)
        first_exp, second_exp = experiments[0], experiments[1]
        self.assertEqual(first_exp[Experiment.experimentid], second_exp[Experiment.experimentid])
        self.assertEqual(first_exp[Experiment.experimentid], TEST_RBNUMBER)
        self.assertNotEqual(first_exp[Experiment.startdate], second_exp[Experiment.startdate])

    def test_GIVEN_data_with_different_dates_WHEN_data_formatted_THEN_experiment_list_contains_both(self):
        rb, date, duration = 2000, datetime(1992, 2, 7), 10
        data = TEST_DATA + [create_data(rb, date, duration)]
        experiments, experiment_teams = reformat_data(data)

        self.assertEqual(len(experiments), 2)
        for entry in experiments:
            if entry[Experiment.experimentid] == TEST_RBNUMBER:
                self.assertEqual(entry[Experiment.startdate], TEST_DATE)
                self.assertEqual(entry[Experiment.duration], TEST_TIMEALLOCATED)
            else:
                self.assertEqual(entry[Experiment.experimentid], rb)
                self.assertEqual(entry[Experiment.startdate], date)
                self.assertEqual(entry[Experiment.duration], duration)

    def test_GIVEN_data_with_local_contacts_and_no_corresponding_date_WHEN_data_formatted_THEN_exception_thrown(self):
        self.assertRaises(KeyError, reformat_data, TEST_CONTACTS)

    def test_GIVEN_data_with_local_contacts_and_corresponding_date_WHEN_data_formatted_THEN_experiment_teams_populated(self):
        experiments, experiment_teams = reformat_data(TEST_DATA)

        expected_user = UserData(TEST_CONTACT_NAME, LOCAL_ORG)
        expected_user_data = ExperimentTeamData(expected_user, LOCAL_ROLE, TEST_RBNUMBER, TEST_DATE)

        self.assertEqual(len(experiment_teams), 1)
        self.assertTrue(expected_user_data == experiment_teams[0])

    def test_GIVEN_user_and_no_corresponding_date_WHEN_data_formatted_THEN_exception_thrown(self):
        team = get_test_experiment_team([TEST_USER_1])
        self.assertRaises(KeyError, reformat_data, [team])

    def test_GIVEN_contact_and_user_and_pi_and_corresponding_date_WHEN_data_formatted_THEN_experiment_teams_populated(self):
        data = [create_web_data_with_experimenters([TEST_USER_1, TEST_USER_PI])]
        experiments, experiment_teams = reformat_data(data)

        expected_user_1 = UserData(TEST_PI_NAME, TEST_PI_ORG)
        expected_user_data_1 = ExperimentTeamData(expected_user_1, TEST_PI_ROLE, TEST_RBNUMBER, TEST_DATE)

        expected_user_2 = UserData(TEST_USER_1_NAME, TEST_USER_1_ORG)
        expected_user_data_2 = ExperimentTeamData(expected_user_2, TEST_USER_1_ROLE, TEST_RBNUMBER, TEST_DATE)

        expected_user_3 = UserData(TEST_CONTACT_NAME, "Science and Technology Facilities Council")
        expected_user_data_3 = ExperimentTeamData(expected_user_3, "Contact", TEST_RBNUMBER, TEST_DATE)

        expected_user_data = [expected_user_data_3, expected_user_data_2, expected_user_data_1]

        self.assertEqual(len(experiment_teams), 3)
        self.assertTrue(expected_user_data == experiment_teams)

    def test_GIVEN_rb_with_multiple_start_dates_WHEN_data_formatted_THEN_two_local_contacts_added(self):
        data = TEST_DATA + [create_data(TEST_RBNUMBER, datetime.now(), 3)]
        experiments, experiment_teams = reformat_data(data)

        self.assertEqual(len(experiment_teams), 2)
        self.assertTrue(experiment_teams[0].user == experiment_teams[1].user)
        self.assertEqual(experiment_teams[0].role, experiment_teams[1].role)
        self.assertEqual(experiment_teams[0].rb_number, experiment_teams[1].rb_number)
        self.assertNotEqual(experiment_teams[0].start_date, experiment_teams[1].start_date)

    def test_GIVEN_rb_with_multiple_start_dates_WHEN_data_formatted_THEN_two_other_users_added(self):
        data = [create_web_data_with_experimenters([TEST_USER_1]), create_web_data_with_experimenters_and_other_date([TEST_USER_1], datetime.now())]
        experiments, experiment_teams = reformat_data(data)

        self.assertEqual(len(experiment_teams), 4)
        self.assertTrue(experiment_teams[1].user == experiment_teams[3].user)
        self.assertEqual(experiment_teams[1].role, experiment_teams[3].role)
        self.assertEqual(experiment_teams[1].rb_number, experiment_teams[3].rb_number)
        self.assertNotEqual(experiment_teams[1].start_date, experiment_teams[3].start_date)

    def test_WHEN_exp_member_created_with_member_role_THEN_becomes_user(self):
        exp_team_data = create_exp_team(MagicMock(), "Member", TEST_RBNUMBER, TEST_DATE)

        self.assertEqual("User", exp_team_data.role)
