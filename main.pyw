from threading import Timer
from exp_db_populator.populator import Populator
from exp_db_populator.mysqlwrapper import MySQLWrapper

rb_tables = Populator(MySQLWrapper("exp_data", "exp_data", "$exp_data", "127.0.0.1"))
rb_tables.file_path = rb_tables.guess_file_name()


def update():
    rb_tables.update()

t = Timer(3600, update())
if rb_tables.file_path != "":
    t.start()
