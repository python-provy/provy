from unittest import TestCase

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian import PipRole


class PipRoleTest(TestCase):
    def setUp(self):
        self.role = PipRole(prov=None, context={})

    @istest
    def extracts_package_name_as_data_from_input(self):
        self.assertEqual(self.role.extract_package_data_from_input('django'), {'name': 'django',})

    @istest
    def extracts_package_name_version_and_equal_to_as_data_from_input(self):
        self.assertEqual(self.role.extract_package_data_from_input('django==1.2.3'), {"name": "django", "version": "1.2.3", "version_constraint": "=="})

    @istest
    def extracts_package_name_version_and_greater_or_equal_to_as_data_from_input(self):
        self.assertEqual(self.role.extract_package_data_from_input("django>=1.2.3"), {"name": "django", "version": "1.2.3", "version_constraint": ">="})

    @istest
    def extracts_package_name_from_specific_repository_path(self):
        self.assertEqual(self.role.extract_package_data_from_input('-e hg+http://bitbucket.org/bkroeze/django-keyedcache/#egg=django-keyedcache'),
                         {"name": "django-keyedcache"})

    @istest
    def extracts_package_name_from_specific_repository_url(self):
        self.assertEqual(self.role.extract_package_data_from_input('http://www.satchmoproject.com/snapshots/trml2pdf-1.2.tar.gz'),
                         {"name": "http://www.satchmoproject.com/snapshots/trml2pdf-1.2.tar.gz"})
