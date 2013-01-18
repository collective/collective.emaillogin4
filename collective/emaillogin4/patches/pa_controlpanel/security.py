import logging
from collections import defaultdict

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five import BrowserView
from zope.component import adapts
from zope.formlib.form import FormFields
from zope.interface import implements
from zope.schema import Bool

import plone.app.controlpanel.security

logger = logging.getLogger('plone.app.controlpanel')


class ISecuritySchema(plone.app.controlpanel.security.ISecuritySchema):

    # In the schema we need a different description.
    use_email_as_login = Bool(
        title=_(u'Use email address as login name'),
        description = _(
            u"Allows users to login with their email address instead "
            u"of specifying a separate login name. This also updates "
            u"the login name of existing users, which may take a "
            u"while on large sites. The login name is saved as "
            u"lower case, but to be userfriendly it does not matter "
            u"which case you use to login. When duplicates are found, "
            u"saving this form will fail. You can use the "
            u"@@migrate-to-emaillogin page to show the duplicates."),
        default=False,
        required=False)

    use_uuid_as_userid = Bool(
        title=_(u'Use UUID user ids'),
        description = _(
            u"Use automatically generated UUIDs as user id for new users. "
            u"When not turned on, the default is to use the same as the "
            u"login name, or when using the email address as login name we "
            u"generate a user id based on the fullname."),
        default=False,
        required=False)


class SecurityControlPanelAdapter(plone.app.controlpanel.security.SecurityControlPanelAdapter):

    adapts(IPloneSiteRoot)
    implements(ISecuritySchema)

    def get_use_email_as_login(self):
        return self.context.getProperty('use_email_as_login')

    def set_use_email_as_login(self, value):
        context = aq_inner(self.context)
        if context.getProperty('use_email_as_login') == value:
            # no change
            return
        if value:
            migrate_to_email_login(self.context)
        else:
            migrate_from_email_login(self.context)

    use_email_as_login = property(get_use_email_as_login,
                                  set_use_email_as_login)

    def get_use_uuid_as_userid(self):
        return self.context.getProperty('use_uuid_as_userid')

    def set_use_uuid_as_userid(self, value):
        self.context.manage_changeProperties(use_uuid_as_userid=value)

    use_uuid_as_userid = property(get_use_uuid_as_userid,
                                  set_use_uuid_as_userid)


def migrate_to_email_login(context):
    # Note that context could be the Plone Site or site_properties.
    pas = getToolByName(context, 'acl_users')
    pprop = getToolByName(context, 'portal_properties')
    site_props = pprop.site_properties
    site_props.manage_changeProperties(use_email_as_login=True)

    # We want the login name to be lowercase here.  This is new in
    # PAS.  Using 'manage_changeProperties' would change the login
    # names immediately, but we want to do that explicitly ourselves
    # and set the lowercase email address as login name, instead of
    # the lower case user id.
    #pas.manage_changeProperties(login_transform='lower')
    pas.login_transform = 'lower'

    # Update the users.
    for user in pas.getUsers():
        if user is None:
            continue
        user_id = user.getUserId()
        email = user.getProperty('email', '')
        if email:
            login_name = pas.applyTransform(email)
            pas.updateLoginName(user_id, login_name)
        else:
            logger.warn("User %s has no email address.", user_id)


def migrate_from_email_login(context):
    # Note that context could be the Plone Site or site_properties.
    pas = getToolByName(context, 'acl_users')
    pprop = getToolByName(context, 'portal_properties')
    site_props = pprop.site_properties
    site_props.manage_changeProperties(use_email_as_login=False)
    # Whether the login name is lowercase or not does not really
    # matter for this use case, but it may be better not to change
    # it at this point.

    # We do want to update the users.
    for user in pas.getUsers():
        if user is None:
            continue
        user_id = user.getUserId()
        # If we keep the transform to lowercase, then we must apply it
        # here as well, otherwise some users will not be able to
        # login, as their user id may be mixed or upper case.
        login_name = pas.applyTransform(user_id)
        pas.updateLoginName(user_id, login_name)


class SecurityControlPanel(plone.app.controlpanel.security.SecurityControlPanel):

    form_fields = FormFields(ISecuritySchema)


class EmailLogin(BrowserView):
    """View to help in migrating to or from using email as login.

    We used to change the login name of existing users here, but that
    is now done by checking or unchecking the option in the security
    control panel.  Here you can only search for duplicates.
    """

    duplicates = []

    def __call__(self):
        if self.request.form.get('check_email'):
            self.duplicates = self.check_email()
        elif self.request.form.get('check_userid'):
            self.duplicates = self.check_userid()
        return self.index()

    @property
    def _email_list(self):
        context = aq_inner(self.context)
        pas = getToolByName(context, 'acl_users')
        emails = defaultdict(list)
        orig_transform = pas.login_transform
        try:
            if not orig_transform:
                # Temporarily set this to lower, as that will happen
                # when turning emaillogin on.
                pas.login_transform = 'lower'
            for user in pas.getUsers():
                if user is None:
                    # Created in the ZMI?
                    continue
                email = user.getProperty('email', '')
                if email:
                    email = pas.applyTransform(email)
                else:
                    logger.warn("User %s has no email address.",
                                user.getUserId())
                    # Add the normal login name anyway.
                    email = pas.applyTransform(user.getUserName())
                emails[email].append(user.getUserId())
        finally:
            pas.login_transform = orig_transform
            return emails

    def check_email(self):
        duplicates = []
        for email, userids in self._email_list.items():
            if len(userids) > 1:
                logger.warn("Duplicate accounts for email address %s: %r",
                            email, userids)
                duplicates.append((email, userids))

        return duplicates

    @property
    def _userid_list(self):
        # user ids are unique, but their lowercase version might not
        # be unique.
        context = aq_inner(self.context)
        pas = getToolByName(context, 'acl_users')
        userids = defaultdict(list)
        orig_transform = pas.login_transform
        try:
            if not orig_transform:
                # Temporarily set this to lower, as that will happen
                # when turning emaillogin on.
                pas.login_transform = 'lower'
            for user in pas.getUsers():
                if user is None:
                    continue
                login_name = pas.applyTransform(user.getUserName())
                userids[login_name].append(user.getUserId())
        finally:
            pas.login_transform = orig_transform
            return userids

    def check_userid(self):
        duplicates = []
        for login_name, userids in self._userid_list.items():
            if len(userids) > 1:
                logger.warn("Duplicate accounts for lower case user id "
                            "%s: %r", login_name, userids)
                duplicates.append((login_name, userids))

        return duplicates

    def switch_to_email(self):
        # This is not used and is only here for backwards
        # compatibility.  It avoids a test failure in
        # Products.CMFPlone.
        migrate_to_email_login(self.context)

    def switch_to_userid(self):
        # This is not used and is only here for backwards
        # compatibility.  It avoids a test failure in
        # Products.CMFPlone.
        migrate_from_email_login(self.context)
