from exp_db_populator.populator import Populator
import epics
import zlib
import json


# PV that contains the instrument list
INST_LIST_PV = "CS:INSTLIST"


class InstrumentPopulatorRunner:
    instruments = {}
    prev_inst_list = None

    def __init__(self):
        self.inst_list_callback(char_value=epics.caget(INST_LIST_PV, as_string=True))
        epics.camonitor(INST_LIST_PV, callback=self.inst_list_callback)

    def inst_list_callback(self, char_value, **kw):
        if char_value != self.prev_inst_list:
            self.prev_inst_list = char_value
            insts_json = zlib.decompress(bytes.fromhex(char_value)).decode("utf-8")
            self.inst_list_changes(json.loads(insts_json))

    def remove_all_populators(self):
        for populator in self.instruments.values():
            populator.running = False
            populator.join()
        self.instruments.clear()

    def inst_list_changes(self, inst_list):
        # Easiest way to make sure all populators are up to date is stop them all and start them again
        self.remove_all_populators()

        for inst in inst_list:
            name, host = inst["name"], inst["hostName"]
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

