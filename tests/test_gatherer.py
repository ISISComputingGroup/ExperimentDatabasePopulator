import unittest
from exp_db_populator.gatherer import Gatherer
from mock import patch
from time import sleep
import threading


class GathererTests(unittest.TestCase):

    def setUp(self):
        self.lock = threading.Lock()

    @patch('exp_db_populator.gatherer.PopulatorOnly')
    @patch('exp_db_populator.gatherer.gather_all_data_and_format')
    def test_GIVEN_instrument_list_has_scheduled_instrument_WHEN_gatherer_started_THEN_populator_created(self, get_data, pop):
        new_name, new_host = "TEST", "NDXTEST"
        inst_list = [{"name": new_name, "hostName": new_host, "isScheduled": True}]
        get_data.return_value = ([], [], {})

        new_gatherer = Gatherer(inst_list, self.lock, False)
        new_gatherer.start()
        sleep(0.5)
        get_data.assert_called()

        pop.assert_called()

    @patch('exp_db_populator.gatherer.PopulatorOnly')
    @patch('exp_db_populator.gatherer.gather_all_data_and_format')
    def test_GIVEN_instrument_list_has_unscheduled_instrument_WHEN_gatherer_started_THEN_populator_not_started(self, get_data, pop):
        new_name, new_host = "TEST", "NDXTEST"
        inst_list = [{"name": new_name, "hostName": new_host, "isScheduled": False}]
        get_data.return_value = ([], [], {})

        new_gatherer = Gatherer(inst_list, self.lock, False)
        new_gatherer.start()
        sleep(0.5)
        get_data.assert_called()

        pop.assert_not_called()
