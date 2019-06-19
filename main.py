
from exp_db_populator.gatherer import Gatherer
import epics
import zlib
import json
import threading
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from six.moves import input
import argparse


# PV that contains the instrument list
INST_LIST_PV = "CS:INSTLIST"

DEBUG = True

log_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs')
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
log_filepath = os.path.join(log_folder, 'Exp_DB_Pop.log')
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        TimedRotatingFileHandler(log_filepath, when='midnight', backupCount=30),
        logging.StreamHandler()
    ]
)


def convert_inst_list(value_from_PV):
    """
    Converts the instrument list coming from the PV into a dictionary.
    Args:
        value_from_PV: The raw value from the PV.
    Returns:
        dict: The instrument information.
    """
    json_string = zlib.decompress(bytes.fromhex(value_from_PV)).decode("utf-8")
    return json.loads(json_string)


def correct_name(old_name):
    """
    Some names are different between IBEX and the web data, this function converts these.
    Args:
        old_name: The IBEX name
    Returns:
        str: The web name
    """
    return "ENGIN-X" if old_name == "ENGINX" else old_name


class InstrumentPopulatorRunner:
    """
    Responsible for managing the thread that will gather the data and populate each instrument.
    """
    gatherers = []
    prev_inst_list = None
    db_lock = threading.RLock()

    def __init__(self, run_continuous=False):
        self.run_continuous = run_continuous

    def start_inst_list_monitor(self):
        logging.info("Setting up monitors on {}".format(INST_LIST_PV))
        self.inst_list_callback(char_value=epics.caget(INST_LIST_PV, as_string=True))
        epics.camonitor(INST_LIST_PV, callback=self.inst_list_callback)

    def inst_list_callback(self, char_value, **kw):
        """
        Called when the instrument list PV changes value.
        Args:
            char_value: The string representation of the PV data.
            **kw: The module will also send other info about the PV, we capture this and don't use it.
        """
        new_inst_list = convert_inst_list(char_value)
        if new_inst_list != self.prev_inst_list:
            self.prev_inst_list = new_inst_list
            self.inst_list_changes(new_inst_list)

    def remove_all_gatherers(self):
        """
        Stops all gatherers and clears the cached list.
        """
        # Faster if all threads are stopped first, then joined after.
        self.wait_for_populators_to_finish()
        for gatherer in self.gatherers:
            gatherer.running = False

        self.wait_for_gatherers_to_finish()

        self.gatherers.clear()

    def inst_list_changes(self, inst_list):
        """
        Starts a new gatherer thread.
        Args:
            inst_list (dict): Information about all instruments.
        """

        # Easiest way to make sure gatherer and populators are up to date is stop them all and start them again
        self.remove_all_gatherers()

        gatherer = Gatherer(inst_list, self.db_lock, self.run_continuous)
        gatherer.start()
        self.gatherers.append(gatherer)

    def wait_for_populators_to_finish(self):
        """
        Blocks until all populators are finished.
        """
        for gatherer in self.gatherers:
            gatherer.remove_all_populators()

    def wait_for_gatherers_to_finish(self):
        """
        Blocks until all gatherers are finished.
        """
        [gatherer.join() for gatherer in self.gatherers]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cont', action='store_true',
                        help="Runs the populator continually, updating periodically. Otherwise run once.")
    args = parser.parse_args()

    main = InstrumentPopulatorRunner(args.cont)
    if DEBUG:
        debug_inst_list = [{"name": "LARMOR", "hostName": "localhost", "isScheduled": True}]
        main.prev_inst_list = debug_inst_list
        main.inst_list_changes(debug_inst_list)
    else:
        main.start_inst_list_monitor()

    if args.cont:
        running = True
        menu_string = 'Enter U to force update from instrument list or Q to Quit\n '

        while running:
            menu_input = input(menu_string).upper()
            if menu_input and isinstance(menu_input, str):
                logging.info("User entered {}".format(menu_input))
                if menu_input == "Q":
                    main.remove_all_gatherers()
                    running = False
                elif menu_input == "U":
                    main.inst_list_changes(main.prev_inst_list)
                else:
                    logging.warning("Command not recognised: {}".format(menu_input))
    else:
        main.wait_for_gatherers_to_finish()
        main.wait_for_populators_to_finish()
