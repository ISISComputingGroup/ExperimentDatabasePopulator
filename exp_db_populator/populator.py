import logging
import threading
from datetime import datetime, timedelta

from peewee import MySQLDatabase, chunked

from exp_db_populator.data_types import CREDS_GROUP, Credentials, RawDataEntry
from exp_db_populator.database_model import Experiment, Experimentteams, User, database_proxy

try:
    from exp_db_populator.passwords.password_reader import get_credentials
except ImportError:
    err = (
        "Password submodule not found, will not be able to write to "
        "databases, unless username/password are specified manually"
    )
    logging.warn(err)

    def get_credentials(group_str: str, entry_str: str) -> Credentials:
        raise EnvironmentError(err)


# How old (in days) the startdate of an experiment must be before it is removed from the database
AGE_OF_EXPIRATION = 100

# Time in seconds between polling the website
POLLING_TIME = 3600


def remove_users_not_referenced() -> None:
    all_team_user_ids = Experimentteams.select(Experimentteams.userid)
    User.delete().where(User.userid.not_in(all_team_user_ids)).execute()  # pyright: ignore (doesn't understand peewee)


def remove_experiments_not_referenced() -> None:
    all_team_experiments = Experimentteams.select(Experimentteams.experimentid)
    Experiment.delete().where(Experiment.experimentid.not_in(all_team_experiments)).execute()  # pyright: ignore (doesn't understand peewee)


def remove_old_experiment_teams(age: float) -> None:
    date = datetime.now() - timedelta(days=age)
    Experimentteams.delete().where(Experimentteams.startdate < date).execute()  # pyright: ignore (doesn't understand peewee)


def create_database(instrument_host: str, credentials: Credentials) -> MySQLDatabase:
    credentials = credentials or get_credentials(CREDS_GROUP, "ExpDatabaseWrite")

    if credentials is None:
        raise ValueError("Cannot connect to db, no credentials.")

    username, password = credentials
    return MySQLDatabase("exp_data", user=username, password=password, host=instrument_host)


def cleanup_old_data() -> None:
    """
    Removes old data from the database.
    """
    remove_old_experiment_teams(AGE_OF_EXPIRATION)
    remove_experiments_not_referenced()
    remove_users_not_referenced()


def populate(experiments: list[RawDataEntry], experiment_teams: list) -> None:
    """
    Populates the database with experiment data.

    Args:
        experiments (list[dict]): A list of dictionaries containing information on experiments.
        experiment_teams (list[exp_db_populator.data_types.ExperimentTeamData]): A list containing
            the users for all new experiments.
    """
    if not experiments or not experiment_teams:
        raise KeyError("Experiment without team or vice versa")

    for batch in chunked(experiments, 100):
        Experiment.insert_many(batch).on_conflict_replace().execute()

    teams_update = [
        {
            Experimentteams.experimentid: exp_team.rb_number,
            Experimentteams.roleid: exp_team.role_id,
            Experimentteams.startdate: exp_team.start_date,
            Experimentteams.userid: exp_team.user.user_id,
        }
        for exp_team in experiment_teams
    ]

    for batch in chunked(teams_update, 100):
        Experimentteams.insert_many(batch).on_conflict_ignore().execute()


def update(
    instrument_name: str,
    instrument_host: str,
    db_lock: threading.RLock,
    instrument_data: tuple[list[RawDataEntry], list[Experimentteams]] | None,
    run_continuous: bool = False,
    credentials: Credentials = None,
) -> None:
    """
    Populates the database with this experiment's data.

    Args:
        instrument_name: The name of the instrument to update.
        instrument_host: The host name of the instrument to update.
        db_lock: A lock for writing to the database.
        instrument_data: The data to send to the instrument, if None the data will just be
            cleared instead.
        run_continuous: Whether the program is running in continuous mode.
        credentials: The credentials to write to the database with, in the form (user, password).
            If None then the credentials are received from the stored git repo
    """
    database = create_database(instrument_host, credentials)
    logging.info(
        "Performing {} update for {}".format(
            "hourly" if run_continuous else "single", instrument_name
        )
    )
    try:
        with db_lock:
            database_proxy.initialize(database)
            if instrument_data is not None:
                experiments, experiment_teams = instrument_data
                populate(experiments, experiment_teams)
            cleanup_old_data()
            database_proxy.initialize(None)  # Ensure no other populators send to the wrong database

        logging.info("{} experiment data updated successfully".format(instrument_name))
    except Exception:
        logging.exception(
            "{} unable to populate database, will try again in {} seconds".format(
                instrument_name, POLLING_TIME
            )
        )
