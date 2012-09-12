from contextlib import contextmanager
import os
import sys
from unittest import TestCase

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian.package.virtualenv import VirtualenvRole


class VirtualenvRoleTest(TestCase):
    @istest
    def refers_to_specific_subdir_at_user_home(self):
        role = VirtualenvRole(prov=None, context={'user': 'johndoe',})

        self.assertEqual(role.base_directory, '/home/johndoe/Envs')

    @istest
    def refers_to_specific_subdir_at_root_home(self):
        role = VirtualenvRole(prov=None, context={'user': 'root',})

        self.assertEqual(role.base_directory, '/root/Envs')