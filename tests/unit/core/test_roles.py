from contextlib import contextmanager
import os
import sys

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.core.roles import Role
from tests.unit.tools.helpers import ProvyTestCase


class RoleTest(ProvyTestCase):
    def setUp(self):
        self.role = Role(prov=None, context={})

    @istest
    def checks_if_a_remote_directory_exists(self):
        with self.execute_mock() as execute:
            execute.return_value = '0'
            self.assertTrue(self.role.remote_exists_dir('/some_path'))

            execute.assert_called_with('test -d /some_path; echo $?', stdout=False, sudo=True)

    @istest
    def checks_if_a_remote_directory_doesnt_exist(self):
        with self.execute_mock() as execute:
            execute.return_value = '1'
            self.assertFalse(self.role.remote_exists_dir('/some_path'))

            execute.assert_called_with('test -d /some_path; echo $?', stdout=False, sudo=True)

    @istest
    def doesnt_create_directory_if_it_already_exists(self):
        with self.mock_role_method('remote_exists_dir') as remote_exists_dir, self.execute_mock() as execute:
            remote_exists_dir.return_value = True
            self.role.ensure_dir('/some_path')
            self.assertFalse(execute.called)

    @istest
    def creates_the_directory_if_it_doesnt_exist(self):
        with self.mock_role_method('remote_exists_dir') as remote_exists_dir, self.execute_mock() as execute:
            remote_exists_dir.return_value = False
            self.role.ensure_dir('/some_path')
            execute.assert_called_with('mkdir -p /some_path', stdout=False, sudo=False)
