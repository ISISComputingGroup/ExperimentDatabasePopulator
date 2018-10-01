from ExperimentData.rbtablesupdater import RBTablesUpdater
import threading
from time import sleep
from ExperimentData.database_model import database
import socket


class main:
    def __init__(self):
        database.init("exp_data", user="exp_data", password="$exp_data", host="127.0.0.1")
        self.rb_tables = RBTablesUpdater(get_instrument_name(socket.gethostname()))
        self.lock = threading.RLock()

    def start_thread(self):
        write_thread = threading.Thread(target=self.do_work, args=())
        write_thread.daemon = True  # Daemonise thread
        write_thread.start()

    def do_work(self):
        while True:
            try:
                print("Performing hourly update")
                with self.lock:
                    self.rb_tables.update(False)
                sleep(3600)
            except Exception as err:
                print(err)

    def force_update(self):
        try:
            with self.lock:
                self.rb_tables.update(True)
        except Exception as err:
            print(err)


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
                main.force_update()
            else:
                print("Command not recognised. Enter M to view menu. ")

