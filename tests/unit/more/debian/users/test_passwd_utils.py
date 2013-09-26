# -*- coding: utf-8 -*-

import unittest
from nose.tools import istest
from mock import patch
from provy.more.debian.users.passwd_utils import random_salt_function, hash_password_function


class PasswdUtilsTest(unittest.TestCase):

    @istest
    def check_if_two_generated_salts_are_different(self):
        """
        Instead of checking if output is truly random, we'll just check if
        in two conseutive calls different functions will be returned
        """
        self.assertNotEqual(random_salt_function(), random_salt_function())

    @istest
    def check_random_add_function_output_is_as_specified(self):
        self.assertEqual(len(random_salt_function(salt_len=125)), 125)

    @istest
    def check_crypt_function_gives_expected_output_for_known_magic_and_salt(self):
        password = "foobarbaz"
        expected_hash = "$6$SqAoXRvk$spgLlL/WL/vcb16ZZ4cMdF5uN90IjH0PpYKdMhqyW.BxXJEVc5RyvnpWcT.OKKJO2vsp32.CWDEd45K6r05bL0"
        salt = "SqAoXRvk"

        self.assertEqual(expected_hash, hash_password_function(password, salt))

    @istest
    def check_crypt_function_uses_random_salt(self):
        password = "foobarbaz"
        expected_hash = "$6$SqAoXRvk$spgLlL/WL/vcb16ZZ4cMdF5uN90IjH0PpYKdMhqyW.BxXJEVc5RyvnpWcT.OKKJO2vsp32.CWDEd45K6r05bL0"
        salt = "SqAoXRvk"

        with patch("provy.more.debian.users.passwd_utils.random_salt_function") as rnd:
            rnd.return_value = salt
            self.assertEqual(expected_hash, hash_password_function(password))
            self.assertTrue(rnd.called)
