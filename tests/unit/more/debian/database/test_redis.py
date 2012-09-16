from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian import AptitudeRole, RedisRole


class RedisRoleTest(TestCase):
    def setUp(self):
        self.role = RedisRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        mock_aptitude = MagicMock(spec=AptitudeRole)

        @contextmanager
        def fake_using(self, klass):
            yield mock_aptitude

        with patch('provy.core.roles.Role.using', fake_using):
            self.role.provision()
            install_calls = mock_aptitude.ensure_package_installed.mock_calls
            self.assertEqual(install_calls, [call('redis-server'), call('python-redis')])