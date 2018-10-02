from ExperimentData.populator import Populator
import threading
from time import sleep
from ExperimentData.database_model import database_proxy
from peewee import MySQLDatabase
import socket


class main:
    def __init__(self):
        database = MySQLDatabase("exp_data", user="exp_data", password="$exp_data", host="127.0.0.1")
        database_proxy.initialize(database)
        self.rb_tables = Populator(get_instrument_name(socket.gethostname()))
        self.lock = threading.RLock()

    def start_thread(self):
        write_thread = threading.Thread(target=self.do_work, args=())
        write_thread.daemon = True  # Daemonise thread
        write_thread.start()

    def update_tables(self):
        try:
            with self.lock:
                self.rb_tables.update()
        except Exception as e:
            print(e)

    def do_work(self):
        while True:
            print("Performing hourly update")
            self.update_tables()
            sleep(3600)


def get_instrument_name(host_name):
    host_name = host_name.upper()
    if host_name == "NDXENGINX":
        return "ENGIN-X"
    else:
        return host_name.replace('NDX', '')


if __name__ == '__main__':
    main = main()
    main.start_thread()

    running = True
    menu_string = 'Enter: M to display menu, U to override the Experiment Database or Q to Quit\n '

    while running:
        menu_input = raw_input(menu_string).upper()
        if menu_input and type(menu_input) == str:
            if menu_input == "Q":
                running = False
            elif menu_input == "M":
                pass
            elif menu_input == "U":
                main.update_tables()
            else:
                print("Command not recognised. Enter M to view menu. ")

