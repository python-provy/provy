from contextlib import contextmanager

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian import AptitudeRole, GitRole
from tests.unit.tools.helpers import ProvyTestCase


class GitRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = GitRole(prov=None, context={})

    @istest
    def ensures_a_repository_is_cloned_as_sudo(self):
        with self.execute_mock() as execute:
            self.role.ensure_repository('some-repo-url', 'working-tree-path')

            execute.assert_called_with('git clone some-repo-url working-tree-path', sudo=True, stdout=False)

    @istest
    def ensures_a_repository_is_cloned_as_non_sudo(self):
        with self.execute_mock() as execute:
            self.role.ensure_repository('some-repo-url', 'working-tree-path', sudo=False)

            execute.assert_called_with('git clone some-repo-url working-tree-path', sudo=False, stdout=False)

    @istest
    def ensures_a_repository_is_cloned_as_specific_user(self):
        with self.execute_mock() as execute, self.mock_role_method('change_dir_owner') as change_dir_owner:
            self.role.ensure_repository('some-repo-url', 'working-tree-path', owner='joe', sudo=False)

            execute.assert_called_with("su -l joe -c 'git clone some-repo-url working-tree-path'", sudo=True, stdout=False)
            change_dir_owner.assert_called_with('working-tree-path', 'joe')
