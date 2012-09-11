from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian import AptitudeRole


class AptitudeRoleTest(TestCase):
    @istest
    def checks_that_a_package_exists(self):
        role = AptitudeRole(prov=None, context={})

        with patch('provy.core.roles.Role.execute') as execute:
            self.assertTrue(role.package_exists('python'))
            execute.assert_called_with('aptitude show python', stdout=False)

    @istest
    def checks_that_a_package_doesnt_exist(self):
        role = AptitudeRole(prov=None, context={})

        with patch('provy.core.roles.Role.execute') as execute:
            execute.return_value = False
            self.assertFalse(role.package_exists('phyton'))
            execute.assert_called_with('aptitude show phyton', stdout=False)