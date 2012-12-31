import os

from mock import patch
from nose.tools import istest

from provy.core.utils import provyfile_path_from, provyfile_module_from
from tests.unit.tools.helpers import ProvyTestCase


class UtilsTest(ProvyTestCase):
    @istest
    def gets_provyfile_path_from_args(self):
        existing_file = 'path/to/provyfile.py'

        with patch.object(os.path, 'exists') as exists:
            exists.return_value = True

            self.assertEqual(provyfile_path_from(args=[existing_file]), existing_file)

    @istest
    def raises_exception_if_file_given_but_not_existant(self):
        existing_file = 'path/to/provyfile.py'

        with patch.object(os.path, 'exists') as exists:
            exists.return_value = False

            self.assertRaises(IOError, provyfile_path_from, args=[existing_file])

    @istest
    def raises_exception_if_file_given_is_absolute(self):
        existing_file = '/path/to/provyfile.py'

        with patch.object(os.path, 'exists') as exists:
            exists.return_value = True

            self.assertRaises(ValueError, provyfile_path_from, args=[existing_file])

    @istest
    def gets_provyfile_as_default_value_if_existant(self):
        with patch.object(os.path, 'exists') as exists:
            exists.side_effect = [True]

            self.assertEqual(provyfile_path_from(args=[]), 'provyfile.py')

    @istest
    def gets_provy_file_as_default_value_if_existant(self):
        with patch.object(os.path, 'exists') as exists:
            exists.side_effect = [False, True]

            self.assertEqual(provyfile_path_from(args=[]), 'provy_file.py')

    @istest
    def raises_exception_if_no_provyfile_is_found(self):
        with patch.object(os.path, 'exists') as exists:
            exists.side_effect = [False, False]

            self.assertRaises(IOError, provyfile_path_from, args=[])

    @istest
    def gets_provyfile_module_from_simple_path(self):
        self.assertEqual(provyfile_module_from('provyfile.py'), 'provyfile')

    @istest
    def gets_provyfile_module_from_nested_path(self):
        self.assertEqual(provyfile_module_from('some/dir/provyfile.py'), 'some.dir.provyfile')

    @istest
    def gets_provyfile_module_from_nested_path_without_extenstion(self):
        self.assertEqual(provyfile_module_from('some/dir/provyfile'), 'some.dir.provyfile')
