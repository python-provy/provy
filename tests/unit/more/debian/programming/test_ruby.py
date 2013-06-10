from nose.tools import istest

from provy.more.debian import AptitudeRole, RubyRole
from provy.more.debian.programming.ruby import UPDATE_ALTERNATIVES_COMMAND
from tests.unit.tools.helpers import ProvyTestCase


class RubyRoleTest(ProvyTestCase):
    def setUp(self):
        super(RubyRoleTest, self).setUp()
        self.role = RubyRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude, self.execute_mock() as execute:
            self.role.provision()

            update_alternatives_command = UPDATE_ALTERNATIVES_COMMAND.format(
                version=self.role.version,
                priority=self.role.priority,
            )
            aptitude.ensure_package_installed.assert_called_once_with('ruby{version}-full'.format(version=self.role.version))
            execute.assert_called_once_with(update_alternatives_command, sudo=True)
