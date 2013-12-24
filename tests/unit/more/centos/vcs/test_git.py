from mock import call
from nose.tools import istest

from provy.more.centos import YumRole, GitRole
from tests.unit.tools.helpers import ProvyTestCase


class GitRoleTest(ProvyTestCase):
    def setUp(self):
        super(GitRoleTest, self).setUp()
        self.role = GitRole(prov=None, context={})

    @istest
    def ensures_a_repository_is_cloned_as_sudo(self):
        with self.execute_mock() as execute:
            self.role.ensure_repository('some-repo-url', 'working-tree-path')

            execute.assert_called_with('git clone some-repo-url working-tree-path', sudo=True, stdout=False, user=None)

    @istest
    def ensures_a_repository_is_cloned_as_non_sudo(self):
        with self.execute_mock() as execute:
            self.role.ensure_repository('some-repo-url', 'working-tree-path', sudo=False)

            execute.assert_called_with('git clone some-repo-url working-tree-path', sudo=False, stdout=False, user=None)

    @istest
    def ensures_a_repository_is_cloned_as_specific_user(self):
        with self.execute_mock() as execute, self.mock_role_method('change_path_owner') as change_path_owner:
            self.role.ensure_repository('some-repo-url', 'working-tree-path', owner='joe', sudo=False)

            execute.assert_called_with('git clone some-repo-url working-tree-path', sudo=False, stdout=False, user='joe')
            change_path_owner.assert_called_with('working-tree-path', 'joe')

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(YumRole) as yum:
            self.role.provision()

            yum.ensure_up_to_date.assert_called_once_with()
            yum.ensure_package_installed.assert_called_once_with('git-core')

    @istest
    def ensures_a_branch_is_checked_out_if_needed(self):
        sudo = 'is it sudo?'
        owner = 'foo-owner'
        branch = 'some-branch'
        with self.mock_role_methods('remote_exists_dir', 'execute', 'change_path_owner'):
            self.role.remote_exists_dir.return_value = True
            self.role.execute.return_value = '# On branch master'

            self.role.ensure_repository('some-repo-url', 'working-tree-path', sudo=sudo, branch=branch, owner=owner)

            self.assertEqual(self.role.execute.mock_calls, [
                call('git --git-dir="working-tree-path/.git" --work-tree="working-tree-path" status', sudo=True, stdout=False),
                call('git --git-dir="working-tree-path/.git" --work-tree="working-tree-path" checkout some-branch', sudo=sudo, user=owner),
            ])
