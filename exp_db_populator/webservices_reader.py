# -*- coding: utf-8 -*-
import logging
import math
import typing
from datetime import datetime, timedelta

import requests
from suds.client import Client

from exp_db_populator.data_types import (
    CREDS_GROUP,
    Credentials,
    Experimenter,
    ExperimentTeamData,
    RawDataEntry,
    RbNumber,
    SessionId,
    UserData,
)
from exp_db_populator.database_model import Experiment

try:
    from exp_db_populator.passwords.password_reader import get_credentials
except ImportError:
    err = "Password submodule not found, will not be able to read from web"

    logging.warn(err)

    def get_credentials(group_str: str, entry_str: str) -> Credentials:
        raise EnvironmentError(err)


LOCAL_ORG = "Science and Technology Facilities Council"
LOCAL_ROLE = "Contact"
RELEVANT_DATE_RANGE = 100  # How many days of data to gather (either side of now)
DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

BUS_APPS_SITE = "https://api.facilities.rl.ac.uk/"
BUS_APPS_AUTH = BUS_APPS_SITE + "users-service/v1/sessions"
BUS_APPS_API = BUS_APPS_SITE + "ws/ScheduleWebService?wsdl"

SUCCESSFUL_LOGIN_STATUS_CODE = 201


def get_start_and_end(date: datetime, time_range_days: int) -> tuple[datetime, datetime]:
    days = timedelta(days=time_range_days)
    return date - days, date + days


def get_experimenters(team: RawDataEntry) -> list[Experimenter]:
    return team.get("experimenters", [])


def create_date_range(client: Client) -> typing.Any:  # noqa ANN401 rpc call
    """
    Creates a date range in a format for the web client to understand.
    """
    date_range = client.factory.create("dateRange")
    start, end = get_start_and_end(datetime.now(), RELEVANT_DATE_RANGE)
    date_range.startDate = start.strftime(DATE_TIME_FORMAT)
    date_range.endDate = end.strftime(DATE_TIME_FORMAT)
    return date_range


def connect() -> tuple[Client, SessionId]:
    """
    Connects to the busapps website.
    Returns:
        tuple: the client and the associated session id.
    """
    try:
        creds = get_credentials(CREDS_GROUP, "WebRead")
        if creds is None:
            raise EnvironmentError("No credentials provided")

        username, password = creds

        response = requests.post(BUS_APPS_AUTH, json={"username": username, "password": password})

        if response.status_code != SUCCESSFUL_LOGIN_STATUS_CODE:
            raise IOError(
                f"Failed to authenticate to busapps web service, "
                f"code={response.status_code}, resp={response.text}"
            )

        session_id = response.json()["sessionId"]
        client = Client(BUS_APPS_API)

        return client, session_id
    except Exception:
        logging.exception("Error whilst trying to connect to web services:")
        raise


def get_all_data_from_web(client: Client, session_id: SessionId) -> list[RawDataEntry]:
    """
    Args:
        client: The client that has connected to the web.
        session_id: The id of the web session.

    Returns:
        list: The data from the website
    """
    try:
        date_range = create_date_range(client)

        logging.info("Gathering updated experiment data from server")
        experiments = client.service.getExperimentsByDate(session_id, "ISIS", date_range)
        return experiments
    except Exception:
        logging.exception("Error gathering data from web services:")
        raise


def create_exp_team(
    user: UserData, role: str, rb_number: RbNumber, date: datetime
) -> ExperimentTeamData:
    # IBEX calls them users, BusApps calls them members
    if role == "Member":
        role = "User"

    return ExperimentTeamData(user, role, rb_number, date)


def reformat_data(
    instrument_data_list: list[RawDataEntry],
) -> tuple[list, list]:
    """
    Reformats the data from the way the website returns it to the way the database wants it.
    Args:
        instrument_data_list (list): List of an instrument's data from the website.

    Returns:
        tuple (list, list): A list of the experiments and their associated data and a
            list of the experiment teams, and a dictionary of rb_numbers and their associated
            instrument.
    """
    try:
        experiments = []
        exp_teams = []

        for data in instrument_data_list:
            experiments.append(
                {
                    Experiment.experimentid: typing.cast(RbNumber, data["rbNumber"]),
                    Experiment.startdate: typing.cast(str, data["scheduledDate"]),
                    Experiment.duration: math.ceil(typing.cast(float, data["timeAllocated"])),
                }
            )

            user_data = UserData(data["lcName"], LOCAL_ORG)
            exp_teams.append(
                create_exp_team(user_data, "Contact", data["rbNumber"], data["scheduledDate"])
            )

            for user in get_experimenters(data):
                user_data = UserData(user["name"], user["organisation"])
                exp_teams.append(
                    create_exp_team(
                        user_data, user["role"], data["rbNumber"], data["scheduledDate"]
                    )
                )

        return experiments, exp_teams
    except Exception:
        logging.exception("Could not reformat data:")
        raise


def gather_data() -> list[RawDataEntry]:
    client, session_id = connect()
    data = get_all_data_from_web(client, session_id)
    return data
