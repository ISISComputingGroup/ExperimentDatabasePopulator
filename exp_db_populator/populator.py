from exp_db_populator.webservices_reader import gather_data_and_format, gather_all_data_and_format
from exp_db_populator.database_model import User, Experiment, Experimentteams, database_proxy
from exp_db_populator.data_types import CREDS_GROUP
from datetime import datetime, timedelta
import threading
from time import sleep
from peewee import MySQLDatabase, chunked
import logging

try:
    from exp_db_populator.passwords.password_reader import get_credentials
except ImportError as e:
    logging.error("Password submodule not found, will not be able to write to databases")

AGE_OF_EXPIRATION = 100  # How old (in days) the startdate of an experiment must be before it is removed from the database
POLLING_TIME = 3600  # Time in seconds between polling the website

def remove_users_not_referenced():
    all_team_user_ids = Experimentteams.select(Experimentteams.userid)
    User.delete().where(User.userid.not_in(all_team_user_ids)).execute()


def remove_experiments_not_referenced():
    all_team_experiments = Experimentteams.select(Experimentteams.experimentid)
    Experiment.delete().where(Experiment.experimentid.not_in(all_team_experiments)).execute()


def remove_old_experiment_teams(age):
    date = datetime.now() - timedelta(days=age)
    Experimentteams.delete().where(Experimentteams.startdate < date).execute()


def create_database(instrument_host):
    username, password = get_credentials(CREDS_GROUP, "ExpDatabaseWrite")
    return MySQLDatabase("exp_data", user=username, password=password, host=instrument_host)


class Populator(threading.Thread):
    running = True

    def __init__(self, instrument_name, instrument_host, db_lock, run_continuous=False):
        threading.Thread.__init__(self)
        self.daemon = True
        self.instrument_host = instrument_host
        self.instrument_name = instrument_name
        self.database = create_database(instrument_host)
        self.run_continuous = run_continuous
        self.db_lock = db_lock
        logging.info("Creating connection to {}".format(instrument_host))

    def populate(self, experiments, experiment_teams):
        """
        Populates the database with experiment data.

        Args:
            experiments (list[dict]): A list of dictionaries containing information on experiments.
            experiment_teams (list[exp_db_populator.data_types.ExperimentTeamData]): A list containing the users for all new experiments.
        """
        if not experiments or not experiment_teams:
            raise KeyError("Experiment without team or vice versa")

        for batch in chunked(experiments, 100):
            Experiment.insert_many(batch).on_conflict_replace().execute()

        teams_update = [{Experimentteams.experimentid: exp_team.rb_number,
                         Experimentteams.roleid: exp_team.role_id,
                         Experimentteams.startdate: exp_team.start_date,
                         Experimentteams.userid: exp_team.user.user_id}
                        for exp_team in experiment_teams]

        for batch in chunked(teams_update, 100):
            Experimentteams.insert_many(batch).on_conflict_ignore().execute()

    def cleanup_old_data(self):
        """
        Removes old data from the database.
        """
        remove_old_experiment_teams(AGE_OF_EXPIRATION)
        remove_experiments_not_referenced()
        remove_users_not_referenced()

    def get_from_web_and_populate(self):
        """
        Gets the data from the web and populates the database.
        """
        experiments, experiment_teams = gather_data_and_format(self.instrument_name)
        with self.db_lock:
            database_proxy.initialize(self.database)
            print(experiments, experiment_teams)
            self.populate(experiments, experiment_teams)
            self.cleanup_old_data()
            database_proxy.initialize(None)  # Ensure no other populators send to the wrong database

    def run(self):
        """
        Periodically runs to populate the database.
        """
        while self.running:
            logging.info("Performing {} update for {}".format("hourly" if self.run_continuous else "single",
                                                              self.instrument_name))
            try:
                self.get_from_web_and_populate()
                logging.info("{} experiment data updated successfully".format(self.instrument_name))
            except Exception:
                logging.exception("{} unable to populate database, will try again in {} seconds".format(
                    self.instrument_name, POLLING_TIME))

            if self.run_continuous:
                for i in range(POLLING_TIME):
                    sleep(1)
                    if not self.running:
                        return
            else:
                break


class PopulatorOnly:

    def __init__(self, instrument_name, instrument_host, db_lock, all_data, run_continuous=False):
        self.daemon = True
        self.instrument_host = instrument_host
        self.instrument_name = instrument_name
        self.database = create_database(instrument_host)
        self.run_continuous = run_continuous
        self.db_lock = db_lock
        self.all_data = all_data
        logging.info("Creating connection to {}".format(instrument_host))

    def populate(self, experiments, experiment_teams):
        """
        Populates the database with experiment data.

        Args:
            experiments (list[dict]): A list of dictionaries containing information on experiments.
            experiment_teams (list[exp_db_populator.data_types.ExperimentTeamData]): A list containing the users for all new experiments.
        """
        if not experiments or not experiment_teams:
            raise KeyError("Experiment without team or vice versa")

        for batch in chunked(experiments, 100):
            Experiment.insert_many(batch).on_conflict_replace().execute()

        teams_update = [{Experimentteams.experimentid: exp_team.rb_number,
                         Experimentteams.roleid: exp_team.role_id,
                         Experimentteams.startdate: exp_team.start_date,
                         Experimentteams.userid: exp_team.user.user_id}
                        for exp_team in experiment_teams]

        for batch in chunked(teams_update, 100):
            Experimentteams.insert_many(batch).on_conflict_ignore().execute()

    def cleanup_old_data(self):
        """
        Removes old data from the database.
        """
        remove_old_experiment_teams(AGE_OF_EXPIRATION)
        remove_experiments_not_referenced()
        remove_users_not_referenced()

    def filter_and_populate(self):
        """
        Populates the database with this experiment's data.
        """
        logging.info("Performing {} update for {}".format("hourly" if self.run_continuous else "single",
                                                          self.instrument_name))
        try:
            experiments, experiment_teams, rb_instrument = self.all_data
            experiments = self.filter_experiments(experiments, rb_instrument)
            experiment_teams = self.filter_experiment_teams(experiment_teams, rb_instrument)
            with self.db_lock:
                database_proxy.initialize(self.database)
                self.populate(experiments, experiment_teams)
                self.cleanup_old_data()
                database_proxy.initialize(None)  # Ensure no other populators send to the wrong database

            logging.info("{} experiment data updated successfully".format(self.instrument_name))
        except Exception:
            logging.exception("{} unable to populate database, will try again in {} seconds".format(
                self.instrument_name, POLLING_TIME))

    def filter_experiments(self, experiments, rb_instrument):
        """
        Returns all of this instrument's experiments data.

        Args:
            experiments (list[dict]): A list of dictionaries containing information on experiments.
            rb_instrument (dict): A dictionary which connects rb numbers with their associated experiment
        """
        return list(filter(lambda x: rb_instrument[x[Experiment.experimentid]] == self.instrument_name, experiments))

    def filter_experiment_teams(self, experiment_teams, rb_instrument):
        """
        Returns all of this instrument's experiment teams data.

        Args:
            experiment_teams (list[exp_db_populator.data_types.ExperimentTeamData]): A list containing the users for all new experiments.
            rb_instrument (dict): A dictionary which connects rb numbers with their associated experiment
        """
        return list(filter(lambda x: rb_instrument[x.rb_number] == self.instrument_name, experiment_teams))
