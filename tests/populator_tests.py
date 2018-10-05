import unittest
import exp_db_populator.database_model as model
from peewee import SqliteDatabase
from exp_db_populator.populator import remove_users_not_referenced, remove_old_experiment_teams, \
    remove_experiments_not_referenced, Populator
from tests.webservices_test_data import *
from mock import Mock, patch
from exp_db_populator.data_types import UserData, ExperimentTeamData


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

        self.populator = Populator("TEST_INST", "test_connection")

        self.addCleanup(patch_db.stop)

    def create_full_record(self, rb_number=TEST_RBNUMBER, user_name=TEST_USER_PI, startdate=TEST_DATE):
        user = model.User.create(name=user_name, organisation="STFC")
        exp = model.Experiment.create(duration=1, experimentid=rb_number, startdate=startdate)
        model.Experimentteams.create(experimentid=exp.experimentid, roleid=self.role.roleid,
                                     startdate=startdate, userid=user.userid)

    def test_GIVEN_user_and_no_experiment_teams_WHEN_unreferenced_removed_THEN_user_removed(self):
        model.User.create(name="John Doe", organisation="STFC")
        self.assertEqual(1, model.User.select().count())

        remove_users_not_referenced()
        self.assertEqual(0, model.User.select().count())

    def test_GIVEN_user_and_unrelated_experiment_teams_WHEN_unreferenced_removed_THEN_user_removed(self):
        model.User.create(name="Delete me", organisation="STFC")
        KEEP_NAME = "Keep Me"
        self.create_full_record(user_name=KEEP_NAME)

        self.assertEqual(2, model.User.select().count())

        remove_users_not_referenced()
        users = model.User.select()
        self.assertEqual(1, users.count())
        self.assertEqual(KEEP_NAME, users[0].name)

    def test_GIVEN_user_and_related_experiment_teams_WHEN_unreferenced_removed_THEN_user_remains(self):
        self.create_full_record(user_name="Keep Me")
        self.assertEqual(1, model.User.select().count())

        remove_users_not_referenced()
        self.assertEqual(1, model.User.select().count())

    def test_GIVEN_experiment_and_no_experiment_teams_WHEN_unreferenced_removed_THEN_experiment_removed(self):
        model.Experiment.create(experimentid=TEST_RBNUMBER, duration=2, startdate=TEST_DATE)
        self.assertEqual(1, model.Experiment.select().count())

        remove_experiments_not_referenced()
        self.assertEqual(0, model.Experiment.select().count())

    def test_GIVEN_experiment_and_unrelated_experiment_teams_WHEN_unreferenced_removed_THEN_experiment_removed(self):
        model.Experiment.create(experimentid=TEST_RBNUMBER, duration=2, startdate=TEST_DATE)
        KEEP_RB = "20000"
        self.create_full_record(rb_number=KEEP_RB)

        self.assertEqual(2, model.Experiment.select().count())

        remove_experiments_not_referenced()
        exps = model.Experiment.select()
        self.assertEqual(1, exps.count())
        self.assertEqual(KEEP_RB, exps[0].experimentid)

    def test_GIVEN_experiment_and_related_experiment_teams_WHEN_unreferenced_removed_THEN_experiment_remains(self):
        self.create_full_record()
        self.assertEqual(1, model.Experiment.select().count())

        remove_experiments_not_referenced()
        self.assertEqual(1, model.Experiment.select().count())

    def test_WHEN_populate_called_with_experiments_and_no_teams_THEN_exception_raised(self):
        self.assertRaises(KeyError, self.populator.populate, ["TEST"], [])

    def create_experiments_dictionary(self):
        return [{model.Experiment.experimentid: TEST_RBNUMBER,
                 model.Experiment.duration: TEST_TIMEALLOCATED,
                 model.Experiment.startdate: TEST_DATE}]

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

    def test_GIVEN_an_old_experiment_WHEN_remove_old_experiments_called_THEN_experiment_teams_removed(self):
        self.create_full_record(startdate=datetime(1980,1,1))

        self.assertEqual(1, model.Experimentteams.select().count())
        remove_old_experiment_teams(1)
        self.assertEqual(0, model.Experimentteams.select().count())

    def test_GIVEN_a_recent_experiment_WHEN_remove_old_experiments_called_THEN_no_data_removed(self):
        self.create_full_record(startdate=datetime.now())

        self.assertEqual(1, model.Experimentteams.select().count())
        remove_old_experiment_teams(1)
        self.assertEqual(1, model.Experimentteams.select().count())
