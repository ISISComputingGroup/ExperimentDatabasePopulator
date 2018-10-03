from exp_db_populator.webservices_reader import gather_data_and_format
from exp_db_populator.database_model import User, Experiment, Experimentteams, database_proxy
from datetime import datetime, timedelta
import threading
from time import sleep
from peewee import MySQLDatabase

AGE_OF_EXPIRATION = 100 # How old (in days) the startdate of an experiment must be before it is removed from the database
POLLING_TIME = 3600 # Time in seconds between polling the website

def remove_users_not_referenced():
    all_team_user_ids = Experimentteams.select(Experimentteams.userid)
    User.delete().where(User.userid.not_in(all_team_user_ids)).execute()


def remove_experiments_not_referenced():
    all_team_experiments = Experimentteams.select(Experimentteams.experimentid)
    Experiment.delete().where(Experiment.experimentid.not_in(all_team_experiments)).execute()


def remove_old_experiment_teams(age):
    date = datetime.now() - timedelta(days=age)
    Experimentteams.delete().where(Experimentteams.startdate < date).execute()


class Populator(threading.Thread):
    running = True

    def __init__(self, instrument_name, instrument_host):
        threading.Thread.__init__(self, daemon=True)
        self.prev_result = ""
        self.instrument_host = instrument_host
        self.instrument_name = instrument_name

        print("Creating connection to {}".format(instrument_host))
        self.database = MySQLDatabase("exp_data", user="exp_write", password="exp_write_pass", host=instrument_host)

    def populate(self, experiments, experiment_teams):
        """
        Populates the database with experiment data.

        Args:
            experiments (list[dict]): A list of dictionaries containing information on experiments.
            experiment_teams (list[exp_db_populator.data_types.ExperimentTeamData]): A list containing the users for all new experiments.
        """
        if not experiments or not experiment_teams:
            raise KeyError("Experiment without team or vice versa")

        teams_update = []

        # TODO: Remove old experiments first

        for exp_team in experiment_teams:
            teams_update.append({Experimentteams.experimentid: exp_team.rb_number,
                                 Experimentteams.roleid: exp_team.role_id,
                                 Experimentteams.startdate: exp_team.start_date,
                                 Experimentteams.userid: exp_team.user.user_id})

        Experiment.insert_many(experiments).on_conflict_replace().execute()
        Experimentteams.insert_many(teams_update).on_conflict_ignore().execute()

    def cleanup_old_data(self):
        remove_old_experiment_teams(AGE_OF_EXPIRATION)
        remove_experiments_not_referenced()
        remove_users_not_referenced()

    def run(self):
        while self.running:
            print("Performing hourly update for {}".format(self.instrument_name))
            try:
                experiments, experiment_teams = gather_data_and_format(self.instrument_name)
                database_proxy.initialize(self.database)
                with database_proxy:
                    self.populate(experiments, experiment_teams)
                    self.cleanup_old_data()
                database_proxy.initialize(None) # Ensure no other populators send to the wrong database
            except Exception as e:
                print("{} unable to populate database: {}".format(self.instrument_name, e))

            print("{} experiment data updated successfully".format(self.instrument_name))
            for i in range(POLLING_TIME):
                sleep(1)
                if not self.running:
                    return
