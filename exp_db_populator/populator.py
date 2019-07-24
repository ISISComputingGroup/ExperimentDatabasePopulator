from exp_db_populator.database_model import User, Experiment, Experimentteams, database_proxy
from exp_db_populator.data_types import CREDS_GROUP
from datetime import datetime, timedelta
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


def cleanup_old_data():
    """
    Removes old data from the database.
    """
    remove_old_experiment_teams(AGE_OF_EXPIRATION)
    remove_experiments_not_referenced()
    remove_users_not_referenced()


def populate(experiments, experiment_teams):
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


def update(instrument_name, instrument_host, db_lock, instrument_data, run_continuous=False):
    """
    Populates the database with this experiment's data.

    Args:
        instrument_name: The name of the instrument to update.
        instrument_host: The host name of the instrument to update.
        db_lock: A lock for writing to the database.
        instrument_data: The data to send to the instrument.
        run_continuous: Whether or not the program is running in continuous mode.
    """
    database = create_database(instrument_host)
    logging.info("Performing {} update for {}".format("hourly" if run_continuous else "single", instrument_name))
    try:
        experiments, experiment_teams = instrument_data
        with db_lock:
            database_proxy.initialize(database)
            populate(experiments, experiment_teams)
            cleanup_old_data()
            database_proxy.initialize(None)  # Ensure no other populators send to the wrong database

        logging.info("{} experiment data updated successfully".format(instrument_name))
    except Exception:
        logging.exception("{} unable to populate database, will try again in {} seconds".format(
            instrument_name, POLLING_TIME))
