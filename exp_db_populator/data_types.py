from datetime import datetime
from typing import NotRequired, TypeAlias, TypedDict

from exp_db_populator.database_model import Role, User

# The group in which the credentials are stored
CREDS_GROUP = "ExpDatabasePopulator"

RbNumber: TypeAlias = str
SessionId: TypeAlias = str


class UserData:
    """
    A class for holding all the data required for a row in the user table.
    """

    def __init__(self, name: str, organisation: str) -> None:
        self.name = name
        self.organisation = organisation

    def __str__(self) -> str:
        return "User {} is from {}".format(self.name, self.organisation)

    @property
    def user_id(self) -> tuple[User, bool]:
        """
        Gets the user id for the user. Will create an entry for the user in
        the database if one doesn't exist.

        Returns: the user's id.
        """
        return User.get_or_create(name=self.name, organisation=self.organisation)[0].userid

    def __eq__(self, other: object) -> bool:
        if isinstance(other, UserData):
            return self.name == other.name and self.organisation == other.organisation
        else:
            return False


class ExperimentTeamData:
    """
    A class for holding all the data required for a row in the experiment team table.
    """

    def __init__(
        self, user: UserData, role: str, rb_number: RbNumber, start_date: datetime
    ) -> None:
        self.user = user
        self.role = role
        self.rb_number = rb_number
        self.start_date = start_date

    @property
    def role_id(self) -> tuple[Role, bool]:
        """
        Gets the role id for the user based on the roles in the database.
        Will raise an exception if role is not found.

        Returns: the role id.

        """
        return Role.get(Role.name == self.role).roleid

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ExperimentTeamData):
            return (
                self.user == other.user
                and self.role == other.role
                and self.rb_number == other.rb_number
                and self.start_date == other.start_date
            )
        else:
            return False


class InstListEntry(TypedDict):
    name: str
    hostName: str
    isScheduled: bool


InstList: TypeAlias = list[InstListEntry]


class Experimenter(TypedDict):
    name: str
    organisation: str
    role: str


class RawDataEntry(TypedDict):
    instrument: str
    lcName: str
    part: int
    rbNumber: str
    scheduledDate: datetime
    timeAllocated: float
    experimenters: NotRequired[list[Experimenter]]


RawData: TypeAlias = dict[str, RawDataEntry]

Credentials: TypeAlias = tuple[str, str] | None
