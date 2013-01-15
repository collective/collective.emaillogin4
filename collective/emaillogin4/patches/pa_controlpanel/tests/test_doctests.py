import doctest
from unittest import TestSuite

from Products.PloneTestCase.PloneTestCase import setupPloneSite
from Testing.ZopeTestCase import FunctionalDocFileSuite

from plone.app.controlpanel.tests.cptc import ControlPanelTestCase
from plone.app.controlpanel.tests.cptc import UserGroupsControlPanelTestCase

setupPloneSite()

OPTIONFLAGS = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


def test_suite():
    tests = ['security.txt',
             ]
    suite = TestSuite()

    for test in tests:
        suite.addTest(FunctionalDocFileSuite(test,
            optionflags=OPTIONFLAGS,
            package="collective.emaillogin4.patches.pa_controlpanel.tests",
            test_class=ControlPanelTestCase))

    return suite
