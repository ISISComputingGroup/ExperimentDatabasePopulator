import unittest

from peewee import SqliteDatabase

import exp_db_populator.database_model as model
from exp_db_populator.data_types import ExperimentTeamData, UserData
from tests.webservices_test_data import *


class UserDataTests(unittest.TestCase):

    def setUp(self):
        # Creates an in-memory database for testing
        database = SqliteDatabase(":memory:")
        model.database_proxy.initialize(database)
        model.database_proxy.create_tables([model.User, model.Experimentteams, model.Experiment, model.Role])
        self.user_data = UserData(TEST_PI_NAME, TEST_PI_ORG)
        self.exp_team_data = ExperimentTeamData(self.user_data, TEST_PI_ROLE, TEST_RBNUMBER, TEST_DATE)

    def test_GIVEN_empty_database_WHEN_user_id_requested_THEN_user_created(self):
        self.assertEqual(0, model.User.select().count())

        self.user_data.user_id

        users = model.User.select()
        self.assertEqual(1, users.count())
        self.assertEqual(TEST_PI_NAME, users[0].name)
        self.assertEqual(TEST_PI_ORG, users[0].organisation)

    def test_GIVEN_user_exists_WHEN_user_id_requested_THEN_no_new_user_created(self):
        model.User.create(name=TEST_PI_NAME, organisation=TEST_PI_ORG)
        self.assertEqual(1, model.User.select().count())

        self.user_data.user_id

        users = model.User.select()
        self.assertEqual(1, users.count())
        self.assertEqual(TEST_PI_NAME, users[0].name)
        self.assertEqual(TEST_PI_ORG, users[0].organisation)

    def test_WHEN_non_existant_role_id_requested_THEN_exception_thrown_and_no_new_role_created(self):
        self.assertEqual(0, model.Role.select().count())

        try:
            self.exp_team_data.role_id
            self.assertTrue(False)
        except model.Role.DoesNotExist:
            self.assertTrue(True)

        self.assertEqual(0, model.Role.select().count())

    def test_WHEN_pre_existing_role_id_requested_THEN_role_id_returned_and_no_new_role_created(self):
        existing_role = model.Role.create(name=TEST_PI_ROLE, priority=1)
        self.assertEqual(1, model.Role.select().count())

        role_id = self.exp_team_data.role_id

        self.assertEqual(1,  model.Role.select().count())
        self.assertEqual(existing_role.roleid, role_id)
