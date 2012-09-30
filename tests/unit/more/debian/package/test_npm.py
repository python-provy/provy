from contextlib import contextmanager

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.core.roles import DistroInfo
from provy.more.debian import AptitudeRole, NodeJsRole, NPMRole
from tests.unit.tools.helpers import ProvyTestCase


class NPMRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = NPMRole(prov=None, context={})

    @istest
    def provisions_node_js_as_dependency(self):
        with self.mock_role_method('provision_role') as provision_role:
            self.role.provision()

            provision_role.assert_called_with(NodeJsRole)
