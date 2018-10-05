from exp_db_populator.populator import Populator
import epics
import zlib
import json
import threading

# Instruments to ignore
IGNORE_LIST = ["DEMO", "MUONFE", "ZOOM", "RIKENFE", "SELAB", "EMMA-A"]

# PV that contains the instrument list
INST_LIST_PV = "CS:INSTLIST"

DEBUG = False

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
    Responsible for managing the threads that will populate each instrument.
    """
    instruments = {}
    prev_inst_list = None
    db_lock = threading.Lock()

    def start_inst_list_monitor(self):
        self.inst_list_callback(char_value=epics.caget(INST_LIST_PV, as_string=True))
        epics.camonitor(INST_LIST_PV, callback=self.inst_list_callback)

    def inst_list_callback(self, char_value, **kw):
        """
        Called when the instrument list PV changes value.
        Args:
            char_value: The string representation of the PV data.
            **kw: The module will also send other info about the PV, we capture this and don't use it.
        """
        if char_value != self.prev_inst_list:
            self.prev_inst_list = char_value
            self.inst_list_changes(convert_inst_list(char_value))

    def remove_all_populators(self):
        """
        Stops all populators and clears the cached list.
        """
        for populator in self.instruments.values():
            populator.running = False
            populator.join()
        self.instruments.clear()

    def inst_list_changes(self, inst_list):
        """
        Starts a new populator thread for each instrument.
        Args:
            inst_list (dict): Information about all instruments.
        """
        # Easiest way to make sure all populators are up to date is stop them all and start them again
        self.remove_all_populators()

        for inst in inst_list:
            name, host = correct_name(inst["name"]), inst["hostName"]
            if name not in IGNORE_LIST:
                try:
                    new_populator = Populator(name, host, self.db_lock)
                    new_populator.start()
                    self.instruments[name] = new_populator
                except Exception as e:
                    print("Unable to connect to {}".format(name))


if __name__ == '__main__':
    main = InstrumentPopulatorRunner()
    if DEBUG:
        main.inst_list_changes([{"name": "LARMOR", "hostName": "localhost"}])
    else:
        main.start_inst_list_monitor()

    running = True
    menu_string = 'Enter: M to display menu, U to force update from instrument list or Q to Quit\n '

    while running:
        menu_input = input(menu_string).upper()
        if menu_input and type(menu_input) == str:
            if menu_input == "Q":
                running = False
            elif menu_input == "M":
                pass
            elif menu_input == "U":
                main.inst_list_changes(main.prev_inst_list)
            else:
                print("Command not recognised. Enter M to view menu. ")

