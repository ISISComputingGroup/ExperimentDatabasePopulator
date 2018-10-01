from threading import Timer
from ExperimentData.rbtablesupdater import RBTablesUpdater
from ExperimentData.mysqlwrapper import MySQLWrapper

rb_tables = RBTablesUpdater(MySQLWrapper("exp_data", "exp_data", "$exp_data", "127.0.0.1"))
rb_tables.file_path = rb_tables.guess_file_name()


def update():
    rb_tables.update()

t = Timer(3600, update())
if rb_tables.file_path != "":
    t.start()
