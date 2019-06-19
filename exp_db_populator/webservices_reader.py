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
RELEVANT_DATE_RANGE = 1  # How many days of data to gather (either side of now)
DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

BUS_APPS_SITE = "https://fitbaweb1.isis.cclrc.ac.uk:8443/"
BUS_APPS_AUTH = BUS_APPS_SITE + "UserOfficeWebService/UserOfficeWebService?wsdl"
BUS_APPS_API = BUS_APPS_SITE + "ScheduleSessionBeanService/ScheduleSessionBean?wsdl"

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


def get_data_from_web(instrument, client, session_id):
    """
    Args:
        instrument: The name of the instrument to get the data for.
        client: The client that has connected to the web.
        session_id: The id of the web session.

    Returns:
        tuple: The teams, dates and local_contacts data
    """
    try:
        date_range = create_date_range(client)

        teams = client.service.getExperimentTeamsForInstrument(session_id, instrument, date_range)
        dates = client.service.getExperimentDatesForInstrument(session_id, instrument, date_range)
        local_contacts = client.service.getExperimentLocalContactsForInstrument(session_id, instrument, date_range)
        return teams, dates, local_contacts
    except Exception:
        logging.exception('Error gathering data from web services:')
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


def create_exp_team(user, role, rb_number, rb_start_dates):
    if rb_number not in rb_start_dates:
        raise KeyError("RB number {} could not be found for {}".format(rb_number, user.name))

    # IBEX calls them users, BusApps calls them members
    if role == "Member":
        role = "User"

    return [ExperimentTeamData(user, role, rb_number, date) for date in rb_start_dates[rb_number]]


def reformat_data(teams, dates, local_contacts):
    """
    Reformats the data from the way the website returns it to the way the database wants it.
    Args:
        teams (list): List of teams related to an experiment .
        dates (list): List of all of the experiments and their dates.
        local_contacts (list): List of local contacts for all experiments.

    Returns:
        tuple (list, list): A list of the experiments and their associated data and a list of the experiment teams.
                            Experiment teams contains information on each experiment and which users are related to it.
    """
    try:
        rb_start_dates = {}
        experiments = []
        exp_teams = []

        for date in dates:
            experiments.append({Experiment.experimentid: date['rbNumber'],
                                Experiment.startdate: date['scheduledDate'],
                                Experiment.duration: math.ceil(date['timeAllocated'])})

            rb_number = date['rbNumber']
            date_for_rb = rb_start_dates.get(rb_number, [])
            rb_start_dates[rb_number] = date_for_rb + [date['scheduledDate']]

        for user in local_contacts:
            user_data = UserData(user['name'], LOCAL_ORG)
            exp_teams.extend(create_exp_team(user_data, "Contact", user['rbNumber'], rb_start_dates))

        for team in teams:
            for user in get_experimenters(team):
                user_data = UserData(user['name'], user['organisation'])
                exp_teams.extend(create_exp_team(user_data, user["role"], team['rbNumber'], rb_start_dates))

        return experiments, exp_teams
    except Exception:
        logging.exception('Could not reformat data:')
        raise


def reformat_all_data(data_list):
    """
    Reformats the data from the way the website returns it to the way the database wants it.
    Args:
        data_list (list): List of all data returned by the website.

    Returns:
        tuple (list, list, dict): A list of the experiments and their associated data, a list of the experiment teams,
                            and a dictionary of rb_numbers and their associated instrument.
                            Experiment teams contains information on each experiment and which users are related to it.
    """
    try:
        rb_start_dates = {}
        experiments = []
        exp_teams = []
        rb_instrument = {}

        for data in data_list:
            rb_number = data['rbNumber']
            rb_instrument[rb_number] = data["instrument"]

            experiments.append({Experiment.experimentid: data['rbNumber'],
                                Experiment.startdate: data['scheduledDate'],
                                Experiment.duration: math.ceil(data['timeAllocated'])})

            date_for_rb = rb_start_dates.get(rb_number, [])
            rb_start_dates[rb_number] = date_for_rb + [data['scheduledDate']]

            user_data = UserData(data['lcName'], LOCAL_ORG)
            exp_teams.extend(create_exp_team(user_data, "Contact", data['rbNumber'], rb_start_dates))

            for user in get_experimenters(data):
                user_data = UserData(user['name'], user['organisation'])
                exp_teams.extend(create_exp_team(user_data, user["role"], data['rbNumber'], rb_start_dates))

        return experiments, exp_teams, rb_instrument
    except Exception:
        logging.exception('Could not reformat data:')
        raise


def gather_data_and_format(instrument_name):
    client, session_id = connect()
    teams, dates, local_contacts = get_data_from_web(instrument_name, client, session_id)
    return reformat_data(teams, dates, local_contacts)


def gather_all_data_and_format():
    client, session_id = connect()
    data = get_all_data_from_web(client, session_id)
    return reformat_all_data(data)

