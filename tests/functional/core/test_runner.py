import os

from mock import patch
from nose.tools import istest

from provy.core.runner import run
import provy.core.utils
from tests.unit.tools.helpers import ProvyTestCase
from tests.functional.fixtures.provyfile import (
    provisions,
    cleanups,
    contexts,
    Role1,
    Role2,
    Role3,
    Role4,
)


class RunnerTest(ProvyTestCase):
    @istest
    def runs_normal_provisioning(self):
        provfile_path = os.path.join('tests', 'functional', 'fixtures', 'provyfile')
        password = 'some-pass'
        extra_options = {
            'password': 'another pass',
        }

        with patch.object(provy.core.utils, 'getpass') as mock_getpass:
            mock_getpass.return_value = 'some-password'
            run(provfile_path, 'test', password, extra_options)
            run(provfile_path, 'test2', password, extra_options)

        self.assertIn(Role1, provisions)
        self.assertIn(Role2, provisions)
        self.assertIn(Role3, provisions)
        self.assertIn(Role4, provisions)

        self.assertIn(Role1, cleanups)
        self.assertIn(Role2, cleanups)
        self.assertIn(Role3, cleanups)
        self.assertIn(Role4, cleanups)

        self.assertIn('foo', contexts[Role1])
        self.assertIn('bar', contexts[Role2])
        self.assertIn('baz', contexts[Role2])
        self.assertIn('bar', contexts[Role3])
        self.assertIn('baz', contexts[Role3])
        self.assertIn('foo', contexts[Role4])
