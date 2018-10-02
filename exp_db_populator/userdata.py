from exp_db_populator.database_model import Role, User


class UserData:
    """
    A class for holding all the data required for a row in the experiment team table.
    """
    def __init__(self, name, organisation, role, rb_number, start_date):
        self.name = name
        self.organisation = organisation
        self.role = role
        self.rb_number = rb_number
        self.start_date = start_date

    def __str__(self):
        return "User {} is from {} and is the {} on {}".format(self.name, self.organisation, self.role, self.rb_number)

    @property
    def user_id(self):
        """
        Gets the user id for the user. Will create an entry for the user in the database if one doesn't exist.

        Returns: the user's id.

        """
        return User.get_or_create(name=self.name, organisation=self.organisation)[0].userid

    @property
    def role_id(self):
        """
        Gets the role id for the user based on the roles in the database. Will raise an exception if role is not found.

        Returns: the role id.

        """
        return Role.get(Role.name == self.role).roleid

    def __eq__(self, other):
        return self.name == other.name and \
               self.organisation == other.organisation and \
               self.role == other.role and \
               self.rb_number == other.rb_number and \
               self.start_date == other.start_date

    def __lt__(self, other):
        return str(self) < str(other)
