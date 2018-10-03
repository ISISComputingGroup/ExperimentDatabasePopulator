from exp_db_populator.populator import Populator


# PV that contains the instrument list
INST_LIST_PV = "CS:INSTLIST"


#def get_instrument_list():
#    inst_list = PV(INST_LIST_PV)

class InstrumentPopulatorRunner:
    instruments = {}
    prev_inst_list = []

    def __init__(self):
        pass

    def remove_all_populators(self):
        for populator in self.instruments.values():
            populator.running = False
            populator.join()
        self.instruments.clear()

    def inst_list_changes(self, inst_list):
        self.prev_inst_list = inst_list

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

