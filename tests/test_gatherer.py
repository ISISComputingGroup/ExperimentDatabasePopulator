import unittest
import exp_db_populator.database_model as model
from peewee import SqliteDatabase
from exp_db_populator.populator import remove_users_not_referenced, remove_old_experiment_teams, \
    remove_experiments_not_referenced, Populator, PopulatorOnly
from exp_db_populator.gatherer import Gatherer
from tests.webservices_test_data import *
from mock import Mock, patch
from exp_db_populator.data_types import UserData, ExperimentTeamData
from time import sleep
import threading


class PopulatorTests(unittest.TestCase):

    def setUp(self):
        # Creates an in-memory database for testing
        database = SqliteDatabase(":memory:")
        model.database_proxy.initialize(database)
        model.database_proxy.create_tables([model.User, model.Experimentteams, model.Experiment, model.Role])
        self.role = model.Role.create(name=TEST_PI_ROLE, priority=1)

        patch_db = patch('exp_db_populator.populator.create_database')
        patch_db.return_value = database
        patch_db.start()

        self.lock = threading.Lock()
        # self.populator = PopulatorOnly(TEST_INSTRUMENT, "test_connection", self.lock, ())
        self.populator = Populator(TEST_INSTRUMENT, "test_connection", self.lock)
        self.gatherer = Gatherer(["TEST_INST"], self.lock)

        self.addCleanup(patch_db.stop)

    def create_full_record(self, rb_number=TEST_RBNUMBER, user_name=TEST_USER_PI, startdate=TEST_DATE):
        user = model.User.create(name=user_name, organisation="STFC")
        exp = model.Experiment.create(duration=1, experimentid=rb_number, startdate=startdate)
        model.Experimentteams.create(experimentid=exp.experimentid, roleid=self.role.roleid,
                                     startdate=startdate, userid=user.userid)

    def test_WHEN_populate_called_with_experiments_and_no_teams_THEN_exception_raised(self):
        self.assertRaises(KeyError, self.populator.populate, ["TEST"], [])

    def create_experiments_dictionary(self):
        return [{model.Experiment.experimentid: TEST_RBNUMBER,
                 model.Experiment.duration: TEST_TIMEALLOCATED,
                 model.Experiment.startdate: TEST_DATE}]

    def create_rb_instrument_dictionary(self):
        return {TEST_RBNUMBER: TEST_INSTRUMENT}

    def create_experiment_teams_dictionary(self):
        exp_team_data = Mock(ExperimentTeamData)
        exp_team_data.rb_number = TEST_RBNUMBER
        exp_team_data.role_id = self.role.roleid
        exp_team_data.start_date = TEST_DATE
        exp_team_data.user = Mock(UserData)
        exp_team_data.user.user_id = 1
        return [exp_team_data]

    def test_WHEN_populate_called_with_experiments_and_no_teams_THEN_exception_raised(self):
        experiments = self.create_experiments_dictionary()
        self.assertRaises(KeyError, self.populator.populate, experiments, [])

    def test_WHEN_populate_called_with_teams_and_no_experiments_THEN_exception_raised(self):
        experiment_teams = self.create_experiment_teams_dictionary()
        self.assertRaises(KeyError, self.populator.populate, [], experiment_teams)

    def test_WHEN_filter_experiments_called_with_experiment_belonging_to_instrument_THEN_experiment_accepted(self):
        experiments = self.create_experiments_dictionary()
        rb_instrument = self.create_rb_instrument_dictionary()
        self.assertEqual(1, len(self.populator.filter_experiments(experiments, rb_instrument)))

    def test_WHEN_filter_experiments_called_with_experiment_not_belonging_to_instrument_THEN_experiment_rejected(self):
        experiments = self.create_experiments_dictionary()
        rb_instrument = {TEST_RBNUMBER: TEST_OTHER_INSTRUMENT}
        self.assertEqual(0, len(self.populator.filter_experiments(experiments, rb_instrument)))

    def test_WHEN_filter_experiment_teams_called_with_team_belonging_to_instrument_THEN_team_accepted(self):
        experiment_teams = self.create_experiment_teams_dictionary()
        rb_instrument = self.create_rb_instrument_dictionary()
        self.assertEqual(1, len(self.populator.filter_experiment_teams(experiment_teams, rb_instrument)))

    def test_WHEN_filter_experiment_teams_called_with_team_not_belonging_to_instrument_THEN_team_rejected(self):
        experiment_teams = self.create_experiment_teams_dictionary()
        rb_instrument = {TEST_RBNUMBER: TEST_OTHER_INSTRUMENT}
        self.assertEqual(0, len(self.populator.filter_experiment_teams(experiment_teams, rb_instrument)))

    def test_WHEN_populate_called_with_list_of_experiments_and_teams_THEN_experiments__and_teams_database_populated(self):
        experiments = self.create_experiments_dictionary()
        experiment_teams = self.create_experiment_teams_dictionary()

        db_experiments = model.Experiment.select()
        db_experiment_teams = model.Experimentteams.select()

        self.assertEqual(0, db_experiments.count())
        self.assertEqual(0, db_experiment_teams.count())

        self.populator.populate(experiments, experiment_teams)

        self.assertEqual(1, db_experiments.count())
        self.assertEqual(1, db_experiment_teams.count())

    def test_GIVEN_experiment_already_exists_WHEN_populate_called_THEN_experiment_is_overriden(self):
        model.Experiment.create(duration=5, experimentid=TEST_RBNUMBER, startdate=TEST_DATE)

        experiments = self.create_experiments_dictionary()
        experiment_teams = self.create_experiment_teams_dictionary()

        self.assertNotEqual(TEST_TIMEALLOCATED, model.Experiment.select()[0].duration)

        self.populator.populate(experiments, experiment_teams)

        db_experiments = model.Experiment.select()
        self.assertEqual(1, db_experiments.count())
        self.assertEqual(TEST_TIMEALLOCATED, db_experiments[0].duration)

    @patch('exp_db_populator.populator.gather_data_and_format')
    def test_GIVEN_db_locked_WHEN_populator_running_THEN_does_not_write_to_db(self, gather):
        gather.side_effect = lambda x: (x, x)

        pop_populate = Mock()

        self.populator.cleanup_old_data = lambda: sleep(1)
        self.populator.populate = pop_populate

        thread_one = threading.Thread(target=self.populator.get_from_web_and_populate)

        with self.lock:
            thread_one.start()
            sleep(0.5)
            gather.assert_called()
            pop_populate.assert_not_called()

        sleep(0.5)
        pop_populate.assert_called()

    @patch('exp_db_populator.populator.gather_data_and_format')
    def test_GIVEN_two_populators_WHEN_one_writing_to_database_THEN_the_other_does_not(self, gather):
        gather.side_effect = lambda x: (x, x)
        second_pop = Populator("SECOND_INST", "test_connection", self.lock)

        pop_populate = Mock()

        self.populator.cleanup_old_data = lambda: sleep(0.5)
        self.populator.populate = pop_populate

        second_pop.cleanup_old_data = Mock()
        second_pop.populate = pop_populate

        thread_one = threading.Thread(target=self.populator.get_from_web_and_populate)
        thread_two = threading.Thread(target=second_pop.get_from_web_and_populate)

        thread_one.start()
        thread_two.start()

        pop_populate.assert_called_once_with(self.populator.instrument_name, self.populator.instrument_name)

        thread_one.join()
        sleep(0.2)
        pop_populate.assert_called_with("SECOND_INST", "SECOND_INST")
