from contextlib import contextmanager
import os
import sys
from unittest import TestCase

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian.package.virtualenv import VirtualenvRole


class VirtualenvRoleTest(TestCase):
    @istest
    def refers_to_specific_subdir_at_home_by_default(self):
        role = VirtualenvRole(prov=None, context={})

        base_dir = os.path.join(os.path.expanduser('~'), 'Envs')

        self.assertEqual(role.base_directory, base_dir)