from Products.PlonePAS.plugins.property import ZODBMutablePropertyProvider


def updateUser(self, user_id, login_name):
    """ Update the login name of the user with id user_id.

    This is a new part of the IUserEnumerationPlugin interface, but
    not interesting for us.
    """
    pass


def updateEveryLoginName(self, quit_on_first_error=True):
    """Update login names of all users to their canonical value.

    This is a new part of the IUserEnumerationPlugin interface, but
    not interesting for us.
    """
    pass


# Note: this has already been added to PlonePAS, but has not been
# released yet.  Also, it is nice not to get warnings about this when
# using a Plone version that does not have the newer PlonePAS.
ZODBMutablePropertyProvider.updateUser = updateUser
ZODBMutablePropertyProvider.updateEveryLoginName = updateEveryLoginName
