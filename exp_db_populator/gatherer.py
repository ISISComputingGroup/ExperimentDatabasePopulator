import logging
import threading
from time import sleep

from exp_db_populator.populator import update
from exp_db_populator.webservices_reader import gather_data, reformat_data

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


def filter_instrument_data(raw_data, inst_name):
    """
    Gets the data associated with the specified instrument.
    Args:
        raw_data: All of the raw data from the website
        inst_name: The name of the instrument whose data you want to get
    Returns:
        list: The data associated with the specified instrument
    """
    return [x for x in raw_data if x['instrument'] == inst_name]


class Gatherer(threading.Thread):
    """
    An instance of this class runs on a thread in the background.
    Every hour, it gathers data from the website and sends it to all of the instruments.
    """
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
            all_data = gather_data()
            for inst in self.inst_list:
                if inst["isScheduled"]:
                    name, host = correct_name(inst["name"]), inst["hostName"]
                    instrument_list = filter_instrument_data(all_data, name)
                    if not instrument_list:
                        logging.error(f"Unable to update {name}, no data found. Expired data will still be cleared.")
                        data_to_populate = None
                    else:
                        data_to_populate = reformat_data(instrument_list)
                    try:
                        update(name, host, self.db_lock, data_to_populate, self.run_continuous)
                    except Exception as e:
                        logging.error("Unable to connect to {}: {}".format(name, e))

            if self.run_continuous:
                for i in range(POLLING_TIME):
                    sleep(1)
                    if not self.running:
                        return
            else:
                break
