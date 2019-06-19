from exp_db_populator.populator import PopulatorOnly
from exp_db_populator.webservices_reader import gather_all_data_and_format
import threading
import logging
from time import sleep

POLLING_TIME = 3600  # Time in seconds between polling the website


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

    def __init__(self, inst_list, db_lock, run_continuous=False):
        threading.Thread.__init__(self)
        self.daemon = True
        self.inst_list = inst_list
        self.run_continuous = run_continuous
        self.db_lock = db_lock
        logging.info("Starting gatherer")

    def run(self):
        """
        Periodically runs to gather new data and populate the databases.
        """
        while self.running:
            inst_list = list(map(lambda x: correct_name(x), self.inst_list))
            all_data = gather_all_data_and_format()

            for inst in inst_list:
                if inst["isScheduled"]:
                    name, host = correct_name(inst["name"]), inst["hostName"]
                    try:
                        new_populator = PopulatorOnly(name, host, self.db_lock, all_data, self.run_continuous)
                        new_populator.filter_and_populate()
                    except Exception as e:
                        logging.error("Unable to connect to {}: {}".format(name, e))

            if self.run_continuous:
                for i in range(POLLING_TIME):
                    sleep(1)
                    if not self.running:
                        return
            else:
                break
