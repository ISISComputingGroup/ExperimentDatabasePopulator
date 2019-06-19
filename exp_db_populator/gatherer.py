from exp_db_populator.populator import Populator, PopulatorOnly
from exp_db_populator.webservices_reader import gather_all_data_and_format
import epics
import zlib
import json
import threading
import logging
from time import sleep
import pickle
from logging.handlers import TimedRotatingFileHandler
import os
from six.moves import input
import argparse

POLLING_TIME = 60  # Time in seconds between polling the website


def correct_name(old_name):
    """
    Some names are different between IBEX and the web data, this function converts these.
    Args:
        old_name: The IBEX name
    Returns:
        str: The web name
    """
    return "ENGIN-X" if old_name == "ENGINX" else old_name


class Gatherer(threading.Thread):
    running = True
    instruments = {}

    def __init__(self, inst_list, db_lock, run_continuous=False):
        threading.Thread.__init__(self)
        self.daemon = True
        self.inst_list = inst_list
        self.run_continuous = run_continuous
        self.db_lock = db_lock
        logging.info("Starting gatherer thread")

    def remove_all_populators(self):
        """
        Stops all populators and clears the cached list.
        """
        # Faster if all threads are stopped first, then joined after.
        for populator in self.instruments.values():
            populator.running = False

        self.wait_for_populators_to_finish()

        self.instruments.clear()

    def wait_for_populators_to_finish(self):
        """
        Blocks until all populators are finished.
        """
        [populator.join() for populator in self.instruments.values()]

    def run(self):
        while self.running:
            inst_list = list(map(lambda x: correct_name(x), self.inst_list))
            all_data = gather_all_data_and_format(inst_list)
            # print("All formatted data:")
            # print(all_data)

            for inst in inst_list:
                if inst["isScheduled"]:
                    name, host = correct_name(inst["name"]), inst["hostName"]
                    try:
                        new_populator = PopulatorOnly(name, host, self.db_lock, all_data, self.run_continuous)
                        new_populator.start()
                        self.instruments[name] = new_populator
                    except Exception as e:
                        logging.error("Unable to connect to {}: {}".format(name, e))

            self.remove_all_populators()
            if self.run_continuous:
                for i in range(POLLING_TIME):
                    sleep(1)
                    if not self.running:
                        return
            else:
                break
