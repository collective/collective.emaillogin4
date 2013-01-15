import doctest
from unittest import TestSuite

from Products.PloneTestCase.PloneTestCase import setupPloneSite
from Testing.ZopeTestCase import FunctionalDocFileSuite

from plone.app.controlpanel.tests.cptc import ControlPanelTestCase

setupPloneSite()

OPTIONFLAGS = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


class SecurityControlPanelTestCase(ControlPanelTestCase):
    """Install collective.emaillogin4.

    This switches on email as login and adds a use_uuid_as_userid property.
    """

    def afterSetUp(self):
        super(SecurityControlPanelTestCase, self).afterSetUp()
        qi = getattr(self.portal, 'portal_quickinstaller')
        qi.installProduct('collective.emaillogin4')


    def loginAsManager(self, user='root', pwd='secret'):
        """points the browser to the login screen and logs in as user root with Manager role."""
        self.browser.open('http://nohost/plone/')
        self.browser.getLink('Log in').click()
        #self.browser.getControl('Login Name').value = user
        self.browser.getControl('E-mail').value = user
        self.browser.getControl('Password').value = pwd
        self.browser.getControl('Log in').click()


def test_suite():
    tests = ['security.txt',
             ]
    suite = TestSuite()

    for test in tests:
        suite.addTest(FunctionalDocFileSuite(test,
            optionflags=OPTIONFLAGS,
            package="collective.emaillogin4.patches.pa_controlpanel.tests",
            test_class=SecurityControlPanelTestCase))

    return suite
