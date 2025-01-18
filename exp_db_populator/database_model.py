from typing import Any, Literal, overload

from peewee import (
    AutoField,
    CharField,
    CompositeKey,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    Proxy,
)

database_proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


class Experiment(BaseModel):
    duration = IntegerField(null=True)
    experimentid = CharField(column_name="experimentID")
    startdate = DateTimeField(column_name="startDate")

    class Meta:  # pyright: ignore
        table_name = "experiment"
        indexes = ((("experimentid", "startdate"), True),)
        primary_key = CompositeKey("experimentid", "startdate")

    @overload
    def __getitem__(self, itm: Literal["duration"]) -> int | None:
        pass

    @overload
    def __getitem__(self, itm: Literal["experimentid"]) -> str:
        pass

    def __getitem__(self, itm: str) -> Any:
        return super().__getitem__(itm)  # pyright: ignore (pyright can't see __getitem__)


class Role(BaseModel):
    name = CharField(null=True)
    priority = IntegerField(null=True)
    roleid = AutoField(column_name="roleID")

    class Meta:  # pyright: ignore
        table_name = "role"

    @overload
    def __getitem__(self, itm: Literal["name"] | Literal["role"]) -> str | None:
        pass

    @overload
    def __getitem__(self, itm: Literal["priority"]) -> int | None:
        pass

    def __getitem__(self, itm: str) -> Any:
        return super().__getitem__(itm)  # pyright: ignore (pyright can't see __getitem__)


class User(BaseModel):
    name = CharField(null=True)
    organisation = CharField(null=True)
    userid = AutoField(column_name="userID")

    class Meta:  # pyright: ignore
        table_name = "user"

    @overload
    def __getitem__(self, itm: Literal["name"] | Literal["organisation"]) -> str:
        pass

    @overload
    def __getitem__(self, itm: Literal["userid"]) -> int:
        pass

    def __getitem__(self, itm: str) -> Any:
        return super().__getitem__(itm)  # pyright: ignore (pyright can't see __getitem__)


class Experimentteams(BaseModel):
    experimentid = ForeignKeyField(
        column_name="experimentID", field="experimentid", model=Experiment
    )
    roleid = ForeignKeyField(column_name="roleID", field="roleid", model=Role)
    startdate = ForeignKeyField(
        backref="experiment_startdate_set",
        column_name="startDate",
        field="startdate",
        model=Experiment,
    )
    userid = ForeignKeyField(column_name="userID", field="userid", model=User)

    class Meta:  # pyright: ignore
        table_name = "experimentteams"
        indexes = (
            (("experimentid", "startdate"), False),
            (("experimentid", "userid", "roleid", "startdate"), True),
        )
        primary_key = CompositeKey("experimentid", "roleid", "startdate", "userid")
