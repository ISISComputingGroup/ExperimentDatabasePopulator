from ExperimentData.database_model import database, Experimentteams, Experiment, User


def remove_users_not_referenced():
    User.delete().where(User.userid.not_in(Experimentteams.select()))


class Populator:
    def __init__(self, reader):
        self.reader = reader

    def populate(self, override=False):
        teams_update = []

        #self.remove_old_experiments()

        for user in self.reader.experiment_teams:
            teams_update.append({Experimentteams.experimentid: user.rb_number,
                                 Experimentteams.roleid: user.role_id,
                                 Experimentteams.startdate: user.start_date,
                                 Experimentteams.userid: user.user_id})
        with database.atomic():
            Experiment.insert_many(self.reader.experiments).on_conflict_ignore().execute()
            Experimentteams.insert_many(teams_update).on_conflict_ignore().execute()

        #self.remove_old_experiments(self.experiment_signatures)
        remove_users_not_referenced()

    @staticmethod
    def remove_old_experiments(age):
        pass
        # db_experiments = connection.execute_query("SELECT experimentID, startDate FROM experiment")
        # for db_signature in db_experiments:
        #     if db_signature not in experiment_signatures:
        #         connection.commit("DELETE FROM experiment WHERE experimentID = '{}' AND startDate = '{}'"
        #                           .format(db_signature[0], db_signature[1]))





