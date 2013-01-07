from Products.CMFCore.utils import getToolByName

import Products.CMFPlone.utils


def set_own_login_name(member, loginname):
    """Allow the user to set his/her own login name.
    """
    pas = getToolByName(member, 'acl_users')
    pas.updateOwnLoginName(loginname)


# Patch it.
Products.CMFPlone.utils.set_own_login_name = set_own_login_name
