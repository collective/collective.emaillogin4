from Products.CMFCore.utils import getToolByName

from plone.app.controlpanel.security import SecurityControlPanelAdapter


def get_use_email_as_login(self):
    return self.context.use_email_as_login


def set_use_email_as_login(self, value):
    if value:
        self.context.manage_changeProperties(use_email_as_login=True)
        # We want the login name to be lowercase here.  This is new in PAS.
        pas = getToolByName(self.context, 'acl_users')
        pas.manage_changeProperties(login_transform='lower')
    else:
        # Whether the login name is lowercase or not does not
        # matter for this use case.
        self.context.manage_changeProperties(use_email_as_login=False)

use_email_as_login = property(get_use_email_as_login,
                              set_use_email_as_login)


# Patch it.
SecurityControlPanelAdapter.get_use_email_as_login = get_use_email_as_login
SecurityControlPanelAdapter.set_use_email_as_login = set_use_email_as_login
SecurityControlPanelAdapter.use_email_as_login = use_email_as_login
