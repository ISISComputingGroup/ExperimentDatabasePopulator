import unittest
import ExperimentData.database_model as model
from peewee import SqliteDatabase
from ExperimentData.populator import remove_users_not_referenced
from webservices_test_data import *


def create_full_record(rb_number, user_name):
    user = model.User.create(name=user_name, organisation="STFC")
    experiment = model.Experiment.create(duration=1, experimentid=rb_number, startdate=TEST_DATE)
    role = model.Role.create(name=TEST_PI_ROLE, priority=1)
    model.Experimentteams.create(experimentid=experiment.experimentid, roleid=role.roleid,
                                 startdate=experiment.startdate, userid=user.userid)


class PopulatorTests(unittest.TestCase):
    def setUp(self):
        # Creates an in-memory database for testing
        database = SqliteDatabase(":memory:")
        model.database_proxy.initialize(database)
        model.database_proxy.create_tables([model.User, model.Experimentteams, model.Experiment, model.Role])

    def test_GIVEN_user_and_no_experiment_teams_WHEN_unreferenced_removed_THEN_user_removed(self):
        model.User.create(name="John Doe", organisation="STFC")
        self.assertEqual(1, model.User.select().count())

        remove_users_not_referenced()
        self.assertEqual(0, model.User.select().count())

    def test_GIVEN_user_and_unrelated_experiment_teams_WHEN_unreferenced_removed_THEN_user_removed(self):
        model.User.create(name="Delete me", organisation="STFC")
        create_full_record(TEST_RBNUMBER, "Keep Me")

        self.assertEqual(2, model.User.select().count())

        remove_users_not_referenced()
        self.assertEqual(1, model.User.select().count())

    def test_GIVEN_user_and_related_experiment_teams_WHEN_unreferenced_removed_THEN_user_remains(self):
        create_full_record(TEST_RBNUMBER, "Keep Me")
        self.assertEqual(1, model.User.select().count())

        remove_users_not_referenced()
        self.assertEqual(1, model.User.select().count())
