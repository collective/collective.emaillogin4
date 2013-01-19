from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.tests.base import MigrationTest

from collective.emaillogin4.patches.pa_upgrade.final import to424_pas_interfaces


class PASUpgradeTest(MigrationTest):

    def test_double_upgrade(self):
        # Check that calling our upgrade twice does no harm.
        to424_pas_interfaces(self.portal)
        to424_pas_interfaces(self.portal)

    def test_upgrade_with_email_login(self):
        pas = getToolByName(self.portal, 'acl_users')
        regtool = getToolByName(self.portal, 'portal_registration')
        regtool.addMember('JOE', 'somepassword')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'JOE')

        # First call.
        to424_pas_interfaces(self.portal)
        self.assertEqual(pas.getProperty('login_transform'), '')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'JOE')

        # If email as login is enabled, we want to use lowercase login
        # names, even when that login name is not an email address.
        ptool = getToolByName(self.portal, 'portal_properties')
        ptool.site_properties.manage_changeProperties(use_email_as_login=True)

        # Second call.
        to424_pas_interfaces(self.portal)
        self.assertEqual(pas.getProperty('login_transform'), 'lower')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'joe')
