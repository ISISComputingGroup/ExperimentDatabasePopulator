from exp_db_populator.webservices_reader import gather_data_and_format
from exp_db_populator.database_model import User, Experiment, Experimentteams, database_proxy
from datetime import datetime, timedelta

AGE_OF_EXPIRATION = 100 # How old (in days) the startdate of an experiment must be before it is removed from the database


def remove_users_not_referenced():
    all_team_user_ids = Experimentteams.select(Experimentteams.userid)
    User.delete().where(User.userid.not_in(all_team_user_ids)).execute()


def remove_experiments_not_referenced():
    all_team_experiments = Experimentteams.select(Experimentteams.experimentid)
    Experiment.delete().where(Experiment.experimentid.not_in(all_team_experiments)).execute()


def remove_old_experiment_teams(age):
    date = datetime.now() - timedelta(days=age)
    Experimentteams.delete().where(Experimentteams.startdate < date).execute()


class Populator:
    def __init__(self, instrument_name):
        self.prev_result = ""
        self.instrument_name = instrument_name

    def populate(self, experiments, experiment_teams):
        """
        Populates the database with experiment data.

        Args:
            experiments (list[dict]): A list of dictionaries containing information on experiments.
            experiment_teams (list[exp_db_populator.userdata.UserData]): A list containing the users for all new experiments.
        """
        if not experiments or not experiment_teams:
            raise KeyError("Experiment without team or vice versa")

        teams_update = []

        # TODO: Remove old experiments first

        for user in experiment_teams:
            teams_update.append({Experimentteams.experimentid: user.rb_number,
                                 Experimentteams.roleid: user.role_id,
                                 Experimentteams.startdate: user.start_date,
                                 Experimentteams.userid: user.user_id})

        with database_proxy.atomic():
            Experiment.insert_many(experiments).on_conflict_replace().execute()
        with database_proxy.atomic():
            Experimentteams.insert_many(teams_update).on_conflict_ignore().execute()

    def cleanup_old_data(self):
        remove_old_experiment_teams(AGE_OF_EXPIRATION)
        remove_experiments_not_referenced()
        remove_users_not_referenced()

    def update(self):
        try:
            database_proxy.connect()
            experiments, experiment_teams = gather_data_and_format(self.instrument_name)
            self.populate(experiments, experiment_teams)
            self.cleanup_old_data()
            database_proxy.close()
        except Exception as e:
            print("Unable to populate database: {}".format(e))

        print("Experiment data updated successfully")
