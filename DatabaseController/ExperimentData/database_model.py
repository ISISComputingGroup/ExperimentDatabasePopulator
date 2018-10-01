from peewee import *
# Model built using peewiz

database_proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


class Experiment(BaseModel):
    duration = IntegerField(null=True)
    experimentid = CharField(column_name='experimentID')
    startdate = DateTimeField(column_name='startDate')

    class Meta:
        table_name = 'experiment'
        indexes = (
            (('experimentid', 'startdate'), True),
        )
        primary_key = CompositeKey('experimentid', 'startdate')


class Role(BaseModel):
    name = CharField(null=True)
    priority = IntegerField(null=True)
    roleid = AutoField(column_name='roleID')

    class Meta:
        table_name = 'role'


class User(BaseModel):
    name = CharField(null=True)
    organisation = CharField(null=True)
    userid = AutoField(column_name='userID')

    class Meta:
        table_name = 'user'


class Experimentteams(BaseModel):
    experimentid = ForeignKeyField(column_name='experimentID', field='experimentid', model=Experiment)
    roleid = ForeignKeyField(column_name='roleID', field='roleid', model=Role)
    startdate = ForeignKeyField(backref='experiment_startdate_set', column_name='startDate', field='startdate', model=Experiment)
    userid = ForeignKeyField(column_name='userID', field='userid', model=User)

    class Meta:
        table_name = 'experimentteams'
        indexes = (
            (('experimentid', 'startdate'), False),
            (('experimentid', 'userid', 'roleid', 'startdate'), True),
        )
        primary_key = CompositeKey('experimentid', 'roleid', 'startdate', 'userid')

