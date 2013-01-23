import logging

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import normalizeString
from Products.statusmessages.interfaces import IStatusMessage
from ZODB.POSException import ConflictError
from plone.app.users.userdataschema import IUserDataSchemaProvider
from plone.protect import CheckAuthenticator
from zope.component import getMultiAdapter
from zope.component import getUtility, getAdapter
from zope.formlib.interfaces import InputErrors
from zope.formlib.interfaces import WidgetInputError
from zope.schema import getFieldNamesInOrder

# Define constants from the Join schema that should be added to the
# vocab of the join fields setting in usergroupssettings controlpanel.
JOIN_CONST = ['username', 'password', 'email', 'mail_me']

# Extra imports:
from zope.component import queryUtility
from Products.PlonePAS.interfaces.plugins import IUserManagement
from plone.app.users.browser.interfaces import IUserIdGenerator
from plone.app.users.browser.interfaces import ILoginNameGenerator

# Number of retries for creating a user id like bob-jones-42:
RENAME_AFTER_CREATION_ATTEMPTS = 100

from plone.app.users.browser.register import BaseRegistrationForm

from utils import uuid_userid_generator


def generate_user_id(self, data):
    """Generate a user id from data.

    We try a few options for coming up with a good user id:

    1. We query a utility, so integrators can register a hook to
       generate a user id using their own logic.

    2. If use_uuid_as_userid is set in the site_properties, we
       generate a uuid.

    3. If a username is given and we do not use email as login,
       then we simply return that username as the user id.

    4. We create a user id based on the full name, if that is
       passed.  This may result in an id like bob-jones-2.

    When the email address is used as login name, we originally
    used the email address as user id as well.  This has a few
    possible downsides, which are the main reasons for the new,
    pluggable approach:

    - It does not work for some valid email addresses.

    - Exposing the email address in this way may not be wanted.

    - When the user later changes his email address, the user id
      will still be his old address.  It works, but may be
      confusing.

    Another possibility would be to simply generate a uuid, but that
    is ugly.  We could certainly try that though: the big plus here
    would be that you then cannot create a new user with the same user
    id as a previously existing user if this ever gets removed.  If
    you would get the same id, this new user would get the same global
    and local roles, if those have not been cleaned up.

    When a user id is chosen, the 'user_id' key of the data gets
    set and the user id is returned.
    """
    generator = queryUtility(IUserIdGenerator)
    if generator:
        userid = generator(data)
        if userid:
            data['user_id'] = userid
            return userid

    portal_props = getToolByName(self.context, 'portal_properties')
    props = portal_props.site_properties
    if props.getProperty('use_uuid_as_userid'):
        userid = uuid_userid_generator()
        data['user_id'] = userid
        return userid

    # We may have a username already.
    userid = data.get('username')
    if userid:
        # If we are not using email as login, then this user name is fine.
        if not props.getProperty('use_email_as_login'):
            data['user_id'] = userid
            return userid

    # First get a default value that we can return if we cannot
    # find anything better.
    default = data.get('username') or data.get('email') or ''
    data['user_id'] = default
    fullname = data.get('fullname')
    if not fullname:
        return default
    userid = normalizeString(fullname)
    # First check that this is a valid member id, regardless of
    # whether a member with this id already exists or not.  We
    # access an underscore attribute of the registration tool, so
    # we take a precaution in case this is ever removed as an
    # implementation detail.
    registration = getToolByName(self.context, 'portal_registration')
    if hasattr(registration, '_ALLOWED_MEMBER_ID_PATTERN'):
        if not registration._ALLOWED_MEMBER_ID_PATTERN.match(userid):
            # If 'bob-jones' is not good then 'bob-jones-1' will not
            # be good either.
            return default
    if registration.isMemberIdAllowed(userid):
        data['user_id'] = userid
        return userid
    # Try bob-jones-1, bob-jones-2, etc.
    idx = 1
    while idx <= RENAME_AFTER_CREATION_ATTEMPTS:
        new_id = "%s-%d" % (userid, idx)
        if registration.isMemberIdAllowed(new_id):
            data['user_id'] = new_id
            return new_id
        idx += 1

    # We cannot come up with a nice id, so we simply return the default.
    return default


def generate_login_name(self, data):
    """Generate a login name from data.

    Usually the login name and user id are the same, but this is
    not necessarily true.  When using the email address as login
    name, we may have a different user id, generated by calling
    the generate_user_id method.

    We try a few options for coming up with a good login name:

    1. We query a utility, so integrators can register a hook to
       generate a login name using their own logic.

    2. If a username is given and we do not use email as login,
       then we simply return that username as the login name.

    3. When using email as login, we use the email address.

    In all cases, we call PAS.applyTransform on the login name, if
    that is defined.  This is a recent addition to PAS, currently
    under development.

    When a login name is chosen, the 'login_name' key of the data gets
    set and the login name is returned.
    """
    pas = getToolByName(self.context, 'acl_users')
    generator = queryUtility(ILoginNameGenerator)
    if generator:
        login_name = generator(data)
        if login_name:
            login_name = pas.applyTransform(login_name)
            data['login_name'] = login_name
            return login_name

    # We may have a username already.
    login_name = data.get('username')
    login_name = pas.applyTransform(login_name)
    data['login_name'] = login_name
    portal_props = getToolByName(self.context, 'portal_properties')
    props = portal_props.site_properties
    use_email_as_login = props.getProperty('use_email_as_login')
    # If we are not using email as login, then this user name is fine.
    if not use_email_as_login:
        return login_name

    # We use email as login.
    login_name = data.get('email')
    login_name = pas.applyTransform(login_name)
    data['login_name'] = login_name
    return login_name


def validate_registration(self, action, data):
    """
    specific business logic for this join form
    note: all this logic was taken directly from the old
    validate_registration.py script in
    Products/CMFPlone/skins/plone_login/join_form_validate.vpy
    """

    # CSRF protection
    CheckAuthenticator(self.request)

    registration = getToolByName(self.context, 'portal_registration')

    errors = super(BaseRegistrationForm, self).validate(action, data)
    # ConversionErrors have no field_name attribute... :-(
    error_keys = [error.field_name for error in errors
                  if hasattr(error, 'field_name')]

    form_field_names = [f.field.getName() for f in self.form_fields]

    portal = getUtility(ISiteRoot)
    portal_props = getToolByName(self.context, 'portal_properties')
    props = portal_props.site_properties
    use_email_as_login = props.getProperty('use_email_as_login')

    # passwords should match
    if 'password' in form_field_names:
        assert('password_ctl' in form_field_names)
        # Skip this check if password fields already have an error
        if not ('password' in error_keys or
                'password_ctl' in error_keys):
            password = self.widgets['password'].getInputValue()
            password_ctl = self.widgets['password_ctl'].getInputValue()
            if password != password_ctl:
                err_str = _(u'Passwords do not match.')
                errors.append(WidgetInputError('password',
                              u'label_password', err_str))
                errors.append(WidgetInputError('password_ctl',
                              u'label_password', err_str))
                self.widgets['password'].error = err_str
                self.widgets['password_ctl'].error = err_str

    # Password field should have a minimum length of 5
    if 'password' in form_field_names:
        # Skip this check if password fields already have an error
        if not 'password' in error_keys:
            password = self.widgets['password'].getInputValue()
            if password:
                # Use PAS to test validity
                err_str = registration.testPasswordValidity(password)
                if err_str:
                    errors.append(WidgetInputError('password',
                                  u'label_password', err_str))
                    self.widgets['password'].error = err_str

    email = ''
    try:
        email = self.widgets['email'].getInputValue()
    except InputErrors, exc:
        # WrongType?
        errors.append(exc)
    if use_email_as_login:
        username_field = 'email'
    else:
        username_field = 'username'

    # The term 'username' is not clear.  It may be the user id or
    # the login name.  So here we try to be explicit.

    # Generate a nice user id and store that in the data.
    user_id = self.generate_user_id(data)
    # Generate a nice login name and store that in the data.
    login_name = self.generate_login_name(data)

    # Do several checks to see if the user id and the login name
    # are valid.
    #
    # Skip these checks if username was already in error list.
    #
    # Note that if we cannot generate a unique user id, it is not
    # necessarily the fault of the username field, but it
    # certainly is the most likely cause in a standard Plone
    # setup.

    if not username_field in error_keys:
        # user id may not be the same as the portal id.
        if user_id == portal.getId():
            err_str = _(u"This username is reserved. Please choose a "
                        "different name.")
            errors.append(WidgetInputError(
                    username_field, u'label_username', err_str))
            self.widgets[username_field].error = err_str

    if not username_field in error_keys:
        # Check if user id is allowed by the member id pattern.
        if not registration.isMemberIdAllowed(user_id):
            err_str = _(u"The login name you selected is already in use "
                        "or is not valid. Please choose another.")
            errors.append(WidgetInputError(
                    username_field, u'label_username', err_str))
            self.widgets[username_field].error = err_str

    # Skip this check if email was already in error list
    if not 'email' in error_keys:
        if 'email' in form_field_names:
            if not registration.isValidEmail(email):
                err_str = _(u'You must enter a valid email address.')
                errors.append(WidgetInputError(
                        'email', u'label_email', err_str))
                self.widgets['email'].error = err_str

    if not username_field in error_keys:
        # Check the uniqueness of the login name, not only when
        # use_email_as_login is true, but always.
        pas = getToolByName(self, 'acl_users')
        results = pas.searchUsers(name=login_name, exact_match=True)
        if results:
            err_str = _(u"The login name you selected is already in use "
                        "or is not valid. Please choose another.")
            errors.append(WidgetInputError(
                    username_field, u'label_username', err_str))
            self.widgets[username_field].error = err_str

    if 'password' in form_field_names and not 'password' in error_keys:
        # Admin can either set a password or mail the user (or both).
        if not (self.widgets['password'].getInputValue() or
                self.widgets['mail_me'].getInputValue()):
            err_str = _('msg_no_password_no_mail_me',
                        default=u"You must set a password or choose to "
                        "send an email.")
            errors.append(WidgetInputError(
                    'password', u'label_password', err_str))
            self.widgets['password'].error = err_str
            errors.append(WidgetInputError(
                    'mail_me', u'label_mail_me', err_str))
            self.widgets['mail_me'].error = err_str
    return errors


def handle_join_success(self, data):
    # portal should be acquisition wrapped, this is needed for the schema
    # adapter below
    portal = getToolByName(self.context, 'portal_url').getPortalObject()
    registration = getToolByName(self.context, 'portal_registration')
    mt = getToolByName(self.context, 'portal_membership')

    # user_id and login_name should be in the data, but let's be safe.
    user_id = data.get('user_id', data.get('username'))
    login_name = data.get('login_name', data.get('username'))
    # I have seen a unicode user id.  I cannot reproduce it, but let's
    # make them strings, otherwise you run into trouble when with
    # plone.session when trying to login.
    if isinstance(user_id, unicode):
        user_id = user_id.encode('utf8')
    if isinstance(login_name, unicode):
        login_name = login_name.encode('utf8')

    # Set the username for good measure, as action_join in the
    # AddUserForm expects it to exist and contain the user id and that
    # method is a bit harder to patch.
    data['username'] = user_id

    # The login name may already be in the form, but not
    # necessarily, for example when using email as login.  This is
    # at least needed for logging in immediately when password
    # reset is bypassed.  We need the login name here, not the
    # user id.
    self.request.form['form.username'] = login_name

    password = data.get('password') or registration.generatePassword()
    if isinstance(password, unicode):
        password = password.encode('utf8')

    try:
        registration.addMember(user_id, password, REQUEST=self.request)
    except (AttributeError, ValueError), err:
        logging.exception(err)
        IStatusMessage(self.request).addStatusMessage(err, type="error")
        return

    if user_id != login_name:
        # The user id differs from the login name.  Set the login
        # name correctly.
        acl_users = getToolByName(self.context, 'acl_users')
        # XXX It would be cleaner to have this in pas.
        for plugin_id, userfolder in acl_users.plugins.listPlugins(IUserManagement):
            if not hasattr(userfolder, 'updateUser'):
                continue
            try:
                userfolder.updateUser(user_id, login_name)
            except KeyError:
                continue
            else:
                break

    # set additional properties using the user schema adapter
    schema = getUtility(IUserDataSchemaProvider).getSchema()

    adapter = getAdapter(portal, schema)
    adapter.context = mt.getMemberById(user_id)

    for name in getFieldNamesInOrder(schema):
        if name in data:
            setattr(adapter, name, data[name])

    if data.get('mail_me') or (portal.validate_email and
                               not data.get('password')):
        # We want to validate the email address (users cannot
        # select their own passwords on the register form) or the
        # admin has explicitly requested to send an email on the
        # 'add new user' form.
        try:
            # When all goes well, this call actually returns the
            # rendered mail_password_response template.  As a side
            # effect, this removes any status messages added to
            # the request so far, as they are already shown in
            # this template.
            response = registration.registeredNotify(user_id)
            return response
        except ConflictError:
            # Let Zope handle this exception.
            raise
        except Exception:
            ctrlOverview = getMultiAdapter((portal, self.request),
                                           name='overview-controlpanel')
            mail_settings_correct = not ctrlOverview.mailhost_warning()
            if mail_settings_correct:
                # The email settings are correct, so the most
                # likely cause of an error is a wrong email
                # address.  We remove the account:
                # Remove the account:
                self.context.acl_users.userFolderDelUsers(
                    [user_id], REQUEST=self.request)
                IStatusMessage(self.request).addStatusMessage(
                    _(u'status_fatal_password_mail',
                      default=u"Failed to create your account: we were "
                      "unable to send instructions for setting a password "
                      "to your email address: ${address}",
                      mapping={u'address': data.get('email', '')}),
                    type='error')
                return
            else:
                # This should only happen when an admin registers
                # a user.  The admin should have seen a warning
                # already, but we warn again for clarity.
                IStatusMessage(self.request).addStatusMessage(
                    _(u'status_nonfatal_password_mail',
                      default=u"This account has been created, but we "
                      "were unable to send instructions for setting a "
                      "password to this email address: ${address}",
                      mapping={u'address': data.get('email', '')}),
                    type='warning')
                return

    return


# Patch it.
BaseRegistrationForm.generate_user_id = generate_user_id
BaseRegistrationForm.generate_login_name = generate_login_name
BaseRegistrationForm.validate_registration = validate_registration
BaseRegistrationForm.handle_join_success = handle_join_success
