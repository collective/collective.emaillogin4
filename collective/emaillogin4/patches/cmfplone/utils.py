from AccessControl import getSecurityManager, Unauthorized
from Products.CMFCore.permissions import ManageUsers
from Products.CMFCore.utils import getToolByName

import Products.CMFPlone.utils


def set_own_login_name(member, loginname):
    """Allow the user to set his/her own login name.

    If you have the Manage Users permission, you can update the login
    name of another member too, though the name of this function is a
    bit weird then.  Historical accident.
    """
    pas = getToolByName(member, 'acl_users')
    mt = getToolByName(member, 'portal_membership')
    if member.getId() == mt.getAuthenticatedMember().getId():
        pas.updateOwnLoginName(loginname)
        return
    secman = getSecurityManager()
    if not secman.checkPermission(ManageUsers, member):
        raise Unauthorized('You can only change your OWN login name.')
    pas.updateLoginName(member.getId(), loginname)


# Patch it.
Products.CMFPlone.utils.set_own_login_name = set_own_login_name
