# -*- coding: utf-8 -*-
from suds.client import Client
import ssl
from exp_db_populator.data_types import UserData, ExperimentTeamData
from datetime import datetime, timedelta
from exp_db_populator.database_model import Experiment
from exp_db_populator.data_types import CREDS_GROUP
import math
import logging

try:
    from exp_db_populator.passwords.password_reader import get_credentials
except ImportError as e:
    logging.error("Password submodule not found, will not be able to read from web")

LOCAL_ORG = "Science and Technology Facilities Council"
LOCAL_ROLE = "Contact"
RELEVANT_DATE_RANGE = 100  # How many days of data to gather (either side of now)
DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

BUS_APPS_SITE = "https://api.facilities.rl.ac.uk/ws/"
BUS_APPS_AUTH = BUS_APPS_SITE + "UserOfficeWebService?wsdl"
BUS_APPS_API = BUS_APPS_SITE + "ScheduleWebService?wsdl"

# This is a workaround because the web service does not have a valid certificate
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context


def get_start_and_end(date, time_range_days):
    days = timedelta(days=time_range_days)
    return date - days, date + days


def get_experimenters(team):
    try:
        return team.experimenters
    except AttributeError:
        return []


def create_date_range(client):
    """
    Creates a date range in a format for the web client to understand.
    """
    date_range = client.factory.create('dateRange')
    start, end = get_start_and_end(datetime.now(), RELEVANT_DATE_RANGE)
    date_range.startDate = start.strftime(DATE_TIME_FORMAT)
    date_range.endDate = end.strftime(DATE_TIME_FORMAT)
    return date_range


def connect():
    """
    Connects to the busapps website.
    Returns:
        tuple: the client and the associated session id.
    """
    try:
        username, password = get_credentials(CREDS_GROUP, "WebRead")

        session_id = Client(BUS_APPS_AUTH).service.login(username, password)
        client = Client(BUS_APPS_API)

        return client, session_id
    except Exception:
        logging.exception('Error whilst trying to connect to web services:')
        raise


def get_all_data_from_web(client, session_id):
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
        logging.exception('Error gathering data from web services:')
        raise


def create_exp_team(user, role, rb_number, date):

    # IBEX calls them users, BusApps calls them members
    if role == "Member":
        role = "User"

    return ExperimentTeamData(user, role, rb_number, date)


def reformat_data(instrument_data_list):
    """
    Reformats the data from the way the website returns it to the way the database wants it.
    Args:
        instrument_data_list (list): List of an instrument's data from the website.

    Returns:
        tuple (list, list): A list of the experiments and their associated data and a list of the experiment teams,
                            and a dictionary of rb_numbers and their associated instrument..
    """
    try:
        experiments = []
        exp_teams = []

        for data in instrument_data_list:

            experiments.append({Experiment.experimentid: data['rbNumber'],
                                Experiment.startdate: data['scheduledDate'],
                                Experiment.duration: math.ceil(data['timeAllocated'])})

            user_data = UserData(data['lcName'], LOCAL_ORG)
            exp_teams.append(create_exp_team(user_data, "Contact", data['rbNumber'], data['scheduledDate']))

            for user in get_experimenters(data):
                user_data = UserData(user['name'], user['organisation'])
                exp_teams.append(create_exp_team(user_data, user["role"], data['rbNumber'], data['scheduledDate']))

        return experiments, exp_teams
    except Exception:
        logging.exception('Could not reformat data:')
        raise


def gather_data():
    client, session_id = connect()
    data = get_all_data_from_web(client, session_id)
    return data
