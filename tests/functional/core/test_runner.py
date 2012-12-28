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
    @skip('Not yet ready')
    @istest
    def runs_normal_provisioning(self):
        provfile_path = os.path.join('tests', 'functional', 'fixtures', 'provyfile')
        server_name = 'test'
        password = 'some-pass'
        extra_options = {
            'custom': 'Option',
        }
        run(provfile_path, server_name, password, extra_options)
