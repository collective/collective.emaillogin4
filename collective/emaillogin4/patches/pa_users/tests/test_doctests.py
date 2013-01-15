import doctest
from unittest import TestSuite

from Testing.ZopeTestCase import FunctionalDocFileSuite
from Products.PloneTestCase.PloneTestCase import setupPloneSite

from plone.app.users.tests import TestCase

setupPloneSite()

OPTIONFLAGS = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


class DocTestCase(TestCase):
    # just here to work around a weird error message
    pass


def test_suite():
    tests = ['email_login.txt',
             ]
    suite = TestSuite()
    for test in tests:
        suite.addTest(FunctionalDocFileSuite(test,
            optionflags=OPTIONFLAGS,
            package="collective.emaillogin4.patches.pa_users.tests",
            test_class=DocTestCase))
    return suite
