from contextlib import contextmanager
import os
import sys
from unittest import skip
import tempfile

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.core.runner import run
from tests.unit.tools.helpers import PROJECT_ROOT, ProvyTestCase
from tests.functional.fixtures.provyfile import (
    provisions,
    cleanups,
    contexts,
    Role1,
    Role2,
    Role3,
)


class RunnerTest(ProvyTestCase):
    @istest
    def runs_normal_provisioning(self):
        provfile_path = os.path.join('tests', 'functional', 'fixtures', 'provyfile')
        server_name = 'test'
        password = 'some-pass'
        run(provfile_path, server_name, password, {})

        self.assertIn(Role1, provisions)
        self.assertIn(Role2, provisions)
        self.assertIn(Role3, provisions)

        self.assertIn(Role1, cleanups)
        self.assertIn(Role2, cleanups)
        self.assertIn(Role3, cleanups)

        self.assertIn('foo', contexts[Role1])
        self.assertIn('bar', contexts[Role2])
        self.assertIn('baz', contexts[Role2])
        self.assertIn('bar', contexts[Role3])
        self.assertIn('baz', contexts[Role3])
