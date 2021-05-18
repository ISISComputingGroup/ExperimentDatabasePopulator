import unittest
from exp_db_populator.gatherer import Gatherer, filter_instrument_data
from mock import patch
from time import sleep
import threading


class GathererTests(unittest.TestCase):

    def setUp(self):
        self.lock = threading.Lock()

    @patch('exp_db_populator.gatherer.update')
    @patch('exp_db_populator.gatherer.gather_data')
    def test_GIVEN_instrument_list_has_scheduled_instrument_WHEN_gatherer_started_THEN_update_runs(self, gather_data,
                                                                                                   update):
        new_name, new_host = "TEST", "NDXTEST"
        inst_list = [{"name": new_name, "hostName": new_host, "isScheduled": True}]
        gather_data.return_value = [{'instrument': "TEST",
                                     'rbNumber': 1,
                                     'scheduledDate': "1-1-1",
                                     'timeAllocated': 1,
                                     'lcName': "TEST",
                                     }]

        new_gatherer = Gatherer(inst_list, self.lock, False)
        new_gatherer.start()
        new_gatherer.join()

        update.assert_called()

    @patch('exp_db_populator.gatherer.update')
    @patch('exp_db_populator.gatherer.gather_data')
    def test_GIVEN_no_data_WHEN_gatherer_started_THEN_no_update(self, gather_data, update):
        new_name, new_host = "TEST", "NDXTEST"
        inst_list = [{"name": new_name, "hostName": new_host, "isScheduled": True}]
        gather_data.return_value = []

        new_gatherer = Gatherer(inst_list, self.lock, False)
        new_gatherer.start()
        new_gatherer.join()

        update.assert_called_with(new_name, new_host, self.lock, None, False)

    @patch('exp_db_populator.gatherer.update')
    @patch('exp_db_populator.gatherer.gather_data')
    def test_GIVEN_instrument_list_has_unscheduled_instrument_WHEN_gatherer_started_THEN_no_update(self, gather_data,
                                                                                                   update):
        new_name, new_host = "TEST", "NDXTEST"
        inst_list = [{"name": new_name, "hostName": new_host, "isScheduled": False}]
        gather_data.return_value = []

        new_gatherer = Gatherer(inst_list, self.lock, False)
        new_gatherer.start()
        new_gatherer.join()

        update.assert_not_called()

    def test_GIVEN_data_of_correct_instrument_WHEN_filter_called_THEN_data_accepted(self):
        inst_name = "TEST_INSTRUMENT"
        data_item = {'instrument': inst_name}
        self.assertEqual(filter_instrument_data([data_item], inst_name), [data_item])

    def test_GIVEN_data_of_other_instrument_WHEN_filter_called_THEN_data_rejected(self):
        inst_name = "TEST_INSTRUMENT"
        other_name = "OTHER_INSTRUMENT"
        data_item = {'instrument': other_name}
        self.assertEqual(filter_instrument_data([data_item], inst_name), [])
