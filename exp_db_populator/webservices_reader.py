# -*- coding: utf-8 -*-
from suds.client import Client
import ssl
import sys
from exp_db_populator.userdata import UserData
from datetime import datetime, timedelta
from keepass import kpdb
from database_model import User, Experiment

LOCAL_ORG = "Science and Technology Facilities Council"
LOCAL_ROLE = "Contact"
RELEVANT_DATE_RANGE = 100  # How many days of data to gather (either side of now)
DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

BUS_APPS_SITE = "https://fitbaweb1.isis.cclrc.ac.uk:8443/"
BUS_APPS_AUTH = BUS_APPS_SITE + "UserOfficeWebService/UserOfficeWebService?wsdl"
BUS_APPS_API = BUS_APPS_SITE + "ScheduleSessionBeanService/ScheduleSessionBean?wsdl"

# Required so that unicode values can be read from files
reload(sys)
sys.setdefaultencoding('utf-8')

# This is a workaround because the web service does not have a valid certificate
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context


def get_credentials():
    try:
        db = kpdb.Database("exp_db_populator/inst_passwords.kdb", "reliablebeam")
        entry = [e for e in db.entries if e.title == u"RBFinder"][0]
        return entry.username, entry.password
    except Exception as e:
        print("Failed to get username and password: {}".format(e))
        raise e


def get_start_and_end(date, time_range_days):
    days = timedelta(days=time_range_days)
    return date - days, date + days


def get_experimenters(team):
    try:
        return team.experimenters
    except AttributeError:
        return []


def get_date_range(client):
    date_range = client.factory.create('dateRange')
    start, end = get_start_and_end(datetime.now(), RELEVANT_DATE_RANGE)
    date_range.startDate = start.strftime(DATE_TIME_FORMAT)
    date_range.endDate = end.strftime(DATE_TIME_FORMAT)
    return date_range


def connect():
    try:
        username, password = get_credentials()

        session_id = Client(BUS_APPS_AUTH).service.login(username, password)
        client = Client(BUS_APPS_API)

        return client, session_id
    except Exception as e:
        print('Error whilst trying to connect to web services: {}'.format(e))
        raise e


def get_data_from_web(instrument, client, session_id):
    try:
        date_range = get_date_range(client)

        teams = client.service.getExperimentTeamsForInstrument(session_id, instrument, date_range)
        dates = client.service.getExperimentDatesForInstrument(session_id, instrument, date_range)
        local_contacts = client.service.getExperimentLocalContactsForInstrument(session_id, instrument, date_range)
        return teams, dates, local_contacts
    except Exception as e:
        print('Error gathering data from web services: {}'.format(e))
        raise e


def reformat_data(teams, dates, local_contacts):
    try:
        start_dates = dict()
        experiments = []
        experiment_teams = []

        # TODO: More validation on incoming data

        for date in dates:
            experiments.append({Experiment.experimentid: date['rbNumber'],
                                Experiment.startdate: date['scheduledDate'],
                                Experiment.duration: date['timeAllocated']})
            start_dates[date['rbNumber']] = date['scheduledDate']

        for user in local_contacts:
            rb_number = user['rbNumber']
            user_data = UserData(user['name'], LOCAL_ORG, "Contact", rb_number, start_dates[rb_number])
            experiment_teams.append(user_data)

        for team in teams:
            rb_number = team['rbNumber']
            for user in get_experimenters(team):
                experiment_teams.append(UserData(user['name'], user['organisation'], user['role'],
                                        rb_number, start_dates[rb_number]))
        return experiments, experiment_teams
    except Exception as e:
        print('Could not reformat data: {}'.format(e))
        raise e


def gather_data_and_format(instrument_name):
    client, session_id = connect()
    teams, dates, local_contacts = get_data_from_web(instrument_name, client, session_id)
    return reformat_data(teams, dates, local_contacts)
