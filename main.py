from exp_db_populator.populator import Populator
import threading
from time import sleep
from exp_db_populator.database_model import database_proxy
from peewee import MySQLDatabase
import socket

# PV that contains the instrument list
INST_LIST_PV = "CS:INSTLIST"





def get_instrument_list():
    inst_list = PV(INST_LIST_PV)

class InstrumentPopulatorRunner:
    instruments = {}

    def __init__(self):
        database = MySQLDatabase("exp_data", user="exp_data", password="$exp_data", host="127.0.0.1")
        database_proxy.initialize(database)
        self.db_lock = threading.Lock() # One global db lock required for peewee
        #self.rb_tables = Populator(get_instrument_name(socket.gethostname()))
        self.rb_tables = Populator("LARMOR", self.db_lock)
        self.rb_tables.start()

    def inst_list_changes(self):
        pass
        # Convert to object
        # If thread running for instrument (and correct machine) then fine
        # Else add thread



def get_instrument_name(host_name):
    host_name = host_name.upper()
    if host_name == "NDXENGINX":
        return "ENGIN-X"
    else:
        return host_name.replace('NDX', '')


if __name__ == '__main__':
    main = InstrumentPopulatorRunner()

    # running = True
    # menu_string = 'Enter: M to display menu, U to override the Experiment Database or Q to Quit\n '
    #
    # while running:
    #     menu_input = raw_input(menu_string).upper()
    #     if menu_input and type(menu_input) == str:
    #         if menu_input == "Q":
    #             running = False
    #         elif menu_input == "M":
    #             pass
    #         elif menu_input == "U":
    #             main.update_tables()
    #         else:
    #             print("Command not recognised. Enter M to view menu. ")

