from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.tests.base import MigrationTest

from collective.emaillogin4.patches.pa_upgrade.final import to424_pas_interfaces


class PASUpgradeTest(MigrationTest):

    def test_double_upgrade(self):
        # A freshly created acl_users is perfectly fine.  An old
        # acl_users will miss the IUpdateLoginNamePlugin.  It is too
        # hard to first break a working PAS and then see if our
        # upgrade fixes it.  Let's at least check that calling our
        # upgrade twice does no harm and leads to the correct end
        # result.
        to424_pas_interfaces(self.portal)
        to424_pas_interfaces(self.portal)

        from Products.PluggableAuthService.interfaces.plugins import \
            IUpdateLoginNamePlugin
        pas = getToolByName(self.portal, 'acl_users')
        self.assertTrue(IUpdateLoginNamePlugin in pas.plugins._plugin_types)
        self.assertEqual(len(pas.plugins.listPlugins(IUpdateLoginNamePlugin)), 1)
        plugin_id, plugin = pas.plugins.listPlugins(IUpdateLoginNamePlugin)[0]
        self.assertEqual(plugin_id, 'source_users')

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
