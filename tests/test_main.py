import unittest

from exp_db_populator.cli import InstrumentPopulatorRunner
from exp_db_populator.gatherer import Gatherer
from mock import Mock, patch


class MainTest(unittest.TestCase):
    def setUp(self):
        self.inst_pop_runner = InstrumentPopulatorRunner()

    @patch("exp_db_populator.cli.Gatherer")
    def test_GIVEN_no_gatherer_running_WHEN_instrument_list_has_new_instrument_THEN_gatherer_starts(
        self, gatherer
    ):
        new_name, new_host = "TEST", "NDXTEST"
        new_gather = gatherer.return_value

        self.inst_pop_runner.inst_list_changes(
            [{"name": new_name, "hostName": new_host, "isScheduled": True}]
        )

        self.assertEqual(new_gather, self.inst_pop_runner.gatherer)

    @patch("exp_db_populator.cli.InstrumentPopulatorRunner.remove_gatherer")
    def test_WHEN_instrument_list_updated_THEN_gatherer_stopped_and_cleared(self, stop):
        new_name, new_host = "TEST", "NDXTEST"
        self.inst_pop_runner.inst_list_changes(
            [{"name": new_name, "hostName": new_host, "isScheduled": True}]
        )

        stop.assert_called()

    def test_GIVEN_existing_gatherer_WHEN_remove_gatherer_called_THEN_gatherer_stopped_and_cleared(
        self,
    ):
        old_gatherer = Mock(Gatherer)
        old_gatherer.running = True
        self.inst_pop_runner.gatherer = old_gatherer

        self.inst_pop_runner.remove_gatherer()

        old_gatherer.join.assert_called()
        self.assertEqual(False, old_gatherer.running)
        self.assertEqual(None, self.inst_pop_runner.gatherer)
