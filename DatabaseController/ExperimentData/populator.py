from ExperimentData.webservices_reader import gather_data_and_format
from ExperimentData.database_model import User, Experiment, Experimentteams, database_proxy


def remove_users_not_referenced():
    all_teams = Experimentteams.select(Experimentteams.userid)
    User.delete().where(User.userid.not_in(all_teams)).execute()


class Populator:
    def __init__(self, instrument_name):
        self.prev_result = ""
        self.instrument_name = instrument_name

    def _populate(self, experiments, experiment_teams):
        teams_update = []

        # TODO: Remove old experiments first

        for user in experiment_teams:
            teams_update.append({Experimentteams.experimentid: user.rb_number,
                                 Experimentteams.roleid: user.role_id,
                                 Experimentteams.startdate: user.start_date,
                                 Experimentteams.userid: user.user_id})
        with database_proxy.atomic():
            Experiment.insert_many(experiments).on_conflict_ignore().execute()
            Experimentteams.insert_many(teams_update).on_conflict_ignore().execute()

        #self.remove_old_experiments(self.experiment_signatures)
        remove_users_not_referenced()

    def update(self, override=False):
        try:
            database_proxy.connect()
            experiments, experiment_teams = gather_data_and_format(self.instrument_name)
            self._populate(experiments, experiment_teams)
            database_proxy.close()
        except Exception as e:
            print("Unable to populate database: {}".format(e))

        print("Experiment data updated successfully")
