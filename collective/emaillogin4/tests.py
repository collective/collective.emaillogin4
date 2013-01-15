from Products.CMFCore.utils import getToolByName
from Products.PloneTestCase.PloneTestCase import PloneTestCase


class EmailLoginTestCase(PloneTestCase):
    """Install collective.emaillogin4.

    There are other ways to do this, but this seems okay.
    """

    def afterSetUp(self):
        super(EmailLoginTestCase, self).afterSetUp()
        qi = getattr(self.portal, 'portal_quickinstaller')
        qi.installProduct('collective.emaillogin4')

    def testEmailAsLogin(self):
        ptool = getToolByName(self.portal, 'portal_properties')
        self.assertTrue(ptool.site_properties.getProperty('use_email_as_login'))

    def testLowerPas(self):
        pas = getToolByName(self.portal, 'acl_users')
        self.assertEqual(pas.getProperty('login_transform'), 'lower')

    def testUuidProperty(self):
        ptool = getToolByName(self.portal, 'portal_properties')
        self.assertTrue(ptool.site_properties.hasProperty('use_uuid_as_userid'))
        self.assertFalse(ptool.site_properties.getProperty('use_uuid_as_userid'))
