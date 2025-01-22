import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from exp_db_populator.webservices_test_data import (
    TEST_USER_1,
    create_web_data_with_experimenters_and_other_date,
)

# Loging must be handled here as some imports might log errors
log_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs")
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
log_filepath = os.path.join(log_folder, "Exp_DB_Pop.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        TimedRotatingFileHandler(log_filepath, when="midnight", backupCount=30),
        logging.StreamHandler(),
    ],
)

import argparse
import json
import threading
import zlib

import epics

from exp_db_populator.gatherer import Gatherer
from exp_db_populator.populator import update
from exp_db_populator.webservices_reader import reformat_data

# PV that contains the instrument list
INST_LIST_PV = "CS:INSTLIST"


def convert_inst_list(value_from_pv):
    """
    Converts the instrument list coming from the PV into a dictionary.
    Args:
        value_from_pv: The raw value from the PV.
    Returns:
        dict: The instrument information.
    """
    json_string = zlib.decompress(bytes.fromhex(value_from_pv)).decode("utf-8")
    return json.loads(json_string)


class InstrumentPopulatorRunner:
    """
    Responsible for managing the thread that will gather the data and populate each instrument.
    """

    gatherer = None
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
            **kw: The module will also send other info about the PV, we capture this and don't
                use it.
        """
        new_inst_list = convert_inst_list(char_value)
        if new_inst_list != self.prev_inst_list:
            self.prev_inst_list = new_inst_list
            self.inst_list_changes(new_inst_list)

    def remove_gatherer(self):
        """
        Stops the gatherer and clears the cache.
        """
        # Faster if thread is stopped first, then joined after.
        if self.gatherer is not None:
            self.gatherer.running = False
            self.wait_for_gatherer_to_finish()
            self.gatherer = None

    def inst_list_changes(self, inst_list):
        """
        Starts a new gatherer thread.
        Args:
            inst_list (list): Information about all instruments.
        """

        # Easiest way to make sure gatherer is up to date is to restart it
        self.remove_gatherer()

        new_gatherer = Gatherer(inst_list, self.db_lock, self.run_continuous)
        new_gatherer.start()
        self.gatherer = new_gatherer

    def wait_for_gatherer_to_finish(self):
        """
        Blocks until gatherer is finished.
        """
        self.gatherer.join()


def main_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cont",
        action="store_true",
        help="Runs the populator continually, updating periodically. Otherwise run once.",
    )
    parser.add_argument(
        "--test_data", action="store_true", help="Puts test data into the local database"
    )
    parser.add_argument(
        "--as_instrument",
        type=str,
        default=None,
        help="Puts the specified instruments data into the local database",
    )
    parser.add_argument(
        "--db_user", type=str, default=None, help="The username to use for writing to the database"
    )
    parser.add_argument(
        "--db_pass", type=str, default=None, help="The password to use for writing to the database"
    )
    args = parser.parse_args()

    main = InstrumentPopulatorRunner(args.cont)
    if args.as_instrument:
        debug_inst_list = [
            {"name": args.as_instrument, "hostName": "localhost", "isScheduled": True}
        ]
        main.prev_inst_list = debug_inst_list
        main.inst_list_changes(debug_inst_list)
    elif args.test_data:
        data = [create_web_data_with_experimenters_and_other_date([TEST_USER_1], datetime.now())]
        if not args.db_user or not args.db_pass:
            raise ValueError("Must specify a username and password if using test data")
        update(
            "localhost",
            "localhost",
            threading.RLock(),
            reformat_data(data),
            credentials=(args.db_user, args.db_pass),
        )
    else:
        main.start_inst_list_monitor()

        if args.cont:
            running = True
            menu_string = "Enter U to force update from instrument list or Q to Quit\n "

            while running:
                menu_input = input(menu_string).upper()
                if menu_input and isinstance(menu_input, str):
                    logging.info("User entered {}".format(menu_input))
                    if menu_input == "Q":
                        main.remove_gatherer()
                        running = False
                    elif menu_input == "U":
                        main.inst_list_changes(main.prev_inst_list)
                    else:
                        logging.warning("Command not recognised: {}".format(menu_input))
        else:
            main.wait_for_gatherer_to_finish()


if __name__ == "__main__":
    main_cli()
