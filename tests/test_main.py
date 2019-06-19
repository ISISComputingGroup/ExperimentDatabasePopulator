import unittest
from mock import patch, Mock
from main import InstrumentPopulatorRunner
from exp_db_populator.populator import Populator
from exp_db_populator.gatherer import Gatherer


class MainTest(unittest.TestCase):
    def setUp(self):
        self.inst_pop_runner = InstrumentPopulatorRunner()

    @patch('main.Gatherer')
    def test_GIVEN_no_gatherer_running_WHEN_instrument_list_has_new_instrument_THEN_gatherer_starts(self, gatherer):
        new_name, new_host = "TEST", "NDXTEST"
        new_gather = gatherer.return_value

        self.inst_pop_runner.inst_list_changes([{"name": new_name, "hostName": new_host, "isScheduled": True}])

        self.assertEqual(new_gather, self.inst_pop_runner.gatherer)

    @patch('main.InstrumentPopulatorRunner.remove_gatherer')
    def test_WHEN_instrument_list_updated_THEN_gatherer_stopped_and_cleared(self, stop):
        new_name, new_host = "TEST", "NDXTEST"
        self.inst_pop_runner.inst_list_changes([{"name": new_name, "hostName": new_host, "isScheduled": True}])

        stop.assert_called()

    def test_GIVEN_existing_gatherer_WHEN_remove_gatherer_called_THEN_gatherer_stopped_and_cleared(self):
        old_gatherer = Mock(Gatherer)
        old_gatherer.running = True
        self.inst_pop_runner.gatherer = old_gatherer

        self.inst_pop_runner.remove_gatherer()

        old_gatherer.join.assert_called()
        self.assertEqual(False, old_gatherer.running)
        self.assertEqual(None, self.inst_pop_runner.gatherer)

    # @patch('main.Populator')
    # def test_GIVEN_empty_list_of_populators_WHEN_instrument_list_has_new_instrument_THEN_added_to_populators(self, populator):
    #     new_name, new_host = "TEST", "NDXTEST"
    #     new_pop = populator.return_value
    #     self.inst_pop_runner.inst_list_changes([{"name": new_name, "hostName": new_host, "isScheduled": True}])
    #
    #     self.assertEqual(1, len(self.inst_pop_runner.instruments))
    #     self.assertEqual(new_pop, self.inst_pop_runner.instruments[new_name])

    # @patch('main.Populator')
    # def test_GIVEN_empty_list_of_populators_WHEN_instrument_list_has_new_unscheduled_instrument_THEN_not_added_to_populators(self, populator):
    #     new_name, new_host = "TEST", "NDXTEST"
    #     new_pop = populator.return_value
    #     self.inst_pop_runner.inst_list_changes([{"name": new_name, "hostName": new_host, "isScheduled": False}])
    #
    #     self.assertEqual(0, len(self.inst_pop_runner.instruments))
    #
    # @patch('main.Populator')
    # @patch('main.InstrumentPopulatorRunner.remove_all_populators')
    # def test_WHEN_instrument_list_updated_THEN_existing_stopped_and_cleared(self, populator, stop_all):
    #     new_name, new_host = "TEST", "NDXTEST"
    #     self.inst_pop_runner.inst_list_changes([{"name": new_name, "hostName": new_host, "isScheduled": True}])
    #
    #     stop_all.assert_called()
    #
    # def test_GIVEN_existing_instruments_WHEN_remove_all_called_THEN_existing_stopped_and_cleared(self):
    #     old_name, old_populator = "TEST", Mock(Populator)
    #     old_populator.running = True
    #     self.inst_pop_runner.instruments[old_name] = old_populator
    #
    #     self.inst_pop_runner.remove_all_populators()
    #
    #     old_populator.join.assert_called()
    #     self.assertEqual(False, old_populator.running)
    #     self.assertEqual(0, len(self.inst_pop_runner.instruments))
