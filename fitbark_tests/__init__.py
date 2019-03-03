import unittest

from .test_api import (
    APITest,
    ResourceAccessTest
)
from .test_auth import Auth2Test
from .test_exceptions import ExceptionTest


def all_tests(consumer_key="", consumer_secret="", user_key=None, user_secret=None):
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ExceptionTest))
    suite.addTest(unittest.makeSuite(Auth2Test))
    suite.addTest(unittest.makeSuite(APITest))
    suite.addTest(unittest.makeSuite(ResourceAccessTest))
    return suite
