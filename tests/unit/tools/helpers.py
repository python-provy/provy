from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch


class ProvyTestCase(TestCase):
    @contextmanager
    def using_stub(self, role):
        mock_role = MagicMock(spec=role)

        @contextmanager
        def stub_using(self, klass):
            yield mock_role

        with patch('provy.core.roles.Role.using', stub_using):
            yield mock_role

    @contextmanager
    def execute_mock(self):
        with patch('provy.core.roles.Role.execute') as execute:
            yield execute
