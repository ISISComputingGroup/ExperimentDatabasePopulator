from exp_db_populator.populator import Populator
import epics
import zlib
import json


IGNORE_LIST = ["DEMO", "MUONFE", "ZOOM", "RIKENFE", "SELAB", "EMMA-A"]

# PV that contains the instrument list
INST_LIST_PV = "CS:INSTLIST"


def convert_inst_list(value_from_PV):
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
    if old_name == "ENGINX":
        return "ENGIN-X"
    else:
        return old_name


class InstrumentPopulatorRunner:
    instruments = {}
    prev_inst_list = None

    def __init__(self):
        self.inst_list_callback(char_value=epics.caget(INST_LIST_PV, as_string=True))
        epics.camonitor(INST_LIST_PV, callback=self.inst_list_callback)

    def inst_list_callback(self, char_value, **kw):
        if char_value != self.prev_inst_list:
            self.prev_inst_list = char_value
            self.inst_list_changes(convert_inst_list(char_value))

    def remove_all_populators(self):
        for populator in self.instruments.values():
            populator.running = False
            populator.join()
        self.instruments.clear()

    def inst_list_changes(self, inst_list):
        # Easiest way to make sure all populators are up to date is stop them all and start them again
        self.remove_all_populators()

        for inst in inst_list:
            name, host = correct_name(inst["name"]), inst["hostName"]
            if name not in IGNORE_LIST:
                try:
                    new_populator = Populator(name, host)
                    new_populator.start()
                    self.instruments[name] = new_populator
                except Exception as e:
                    print("Unable to connect to {}".format(name))


if __name__ == '__main__':
    main = InstrumentPopulatorRunner()
    main.inst_list_changes([{"name": "LARMOR", "hostName": "localhost"}])

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

