# A helper test that will compare data web data for each instrument with the data currently on the instrument.
# Useful for testing against the old system
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from main import convert_inst_list, INST_LIST_PV, correct_name
from mock import patch
import epics
from exp_db_populator.populator import Populator
from peewee import SqliteDatabase, MySQLDatabase
import exp_db_populator.database_model as model
import csv
from datetime import datetime


def get_data():
    exps = model.Experiment.select().order_by(model.Experiment.experimentid, model.Experiment.startdate).dicts().execute()
    users = model.User.select().order_by(model.User.name).dicts().execute()
    exp_teams = model.Experimentteams.select().order_by(model.Experimentteams.experimentid,
                                                        model.Experimentteams.startdate,
                                                        model.Experimentteams.roleid).dicts().execute()
    return {"EXPERIMENT": exps, "USERS": users, "EXP_TEAMS": exp_teams}


def write_data_to_file(instrument, data_source, data):
    for k, v in data.items():
        with open("data\{}_{}_{}.csv".format(instrument, k, data_source), 'w') as out:
            dict_writer = csv.DictWriter(out, v[0].keys())
            dict_writer.writeheader()
            dict_writer.writerows(v)


def get_real_data(inst_host):
    db = MySQLDatabase("exp_data", user="report", password="$report", host=inst_host)
    model.database_proxy.initialize(db)

    return get_data()


def record_the_same(real, web, fields):
    for field in fields:
        # Correction as sqllite does not have datetime fields
        if field == 'startdate' and type(web[field]) != datetime:
            web[field] = datetime.strptime(web[field][0:-6], '%Y-%m-%d %H:%M:%S')
        # New version will fill in local facility
        if field == 'organisation' and real[field] == '':
            web[field] = ''
        if real[field] != web[field]:
            return False
    return True


def check_data(inst, real_data, web_data, table, fields):
    real_exps, web_exps = real_data[table], web_data[table]

    # Note this wont find cases where there is stuff missing from the web version but as the inst databases do not clean
    # fully we cannot test this

    # This may also be wrong if something has recently been added to the web service and has not been updated on the
    # instrument yet
    try:
        real_idx = 0
        for web in web_exps:
            real = real_exps[real_idx]
            while not record_the_same(real, web, fields):
                real_idx += 1
                real = real_exps[real_idx]
    except Exception:
        print ("ERROR: Comparison failed for {} on {}".format(table, inst))

inst_list = convert_inst_list(epics.caget(INST_LIST_PV, as_string=True))

for inst in inst_list:
    inst["name"] = correct_name(inst["name"])
    if not inst["isScheduled"]:
        continue

    in_memory_db = SqliteDatabase(":memory:")
    with patch("exp_db_populator.populator.create_database") as create_db:
        create_db.return_value = in_memory_db
        model.database_proxy.initialize(in_memory_db)
        model.database_proxy.create_tables([model.User, model.Experimentteams, model.Experiment, model.Role])
        model.Role.create(name="PI", priority=2, userid=1)
        model.Role.create(name="User", priority=1, userid=2)
        model.Role.create(name="Contact", priority=0, userid=3)

        print("Getting web data for {}".format(inst["name"]))

        populator = Populator(inst["name"], ":memory:", None)
        populator.get_from_web_and_populate()

        web_data = get_data()
        write_data_to_file(inst["name"], "web", web_data)


        print("Getting real data for {}".format(inst["name"]))
        real_data = get_real_data(inst["hostName"])
        write_data_to_file(inst["name"], "real", real_data)

        check_data(inst["name"], real_data, web_data, "EXPERIMENT", ['duration', 'experimentid', 'startdate'])

        check_data(inst["name"], real_data, web_data, "USERS", ['name', 'organisation'])

        check_data(inst["name"], real_data, web_data, "EXP_TEAMS", ['experimentid', 'roleid', 'startdate'])