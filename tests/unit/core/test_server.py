# -*- coding: utf-8 -*-

import unittest
from provy.core.server import ProvyServer


class TestServer(unittest.TestCase):

    def test_init(self):
        roles = (object, object)
        server = ProvyServer("foo", "testserver", "user", roles)
        self.assertIsNone(server.password)
        self.assertIsInstance(server.roles, list)

    def test_getstste(self):
        roles = (object, object)
        server = ProvyServer("foo", "testserver", "user", roles)
        self.assertEqual(
            server.__getstate__(),
            {'address': 'testserver',
             'name': 'foo',
              'options': {},
              'roles': list(roles),
              'ssh_key': None,
              'user': 'user'})

    def test_getstste_with_password(self):
        roles = (object, object)
        server = ProvyServer("foo", "testserver", "user", roles, password="pass")
        self.assertEqual(
            server.__getstate__(),
            {'address': 'testserver',
             'name': 'foo',
              'options': {},
              'roles': list(roles),
              'ssh_key': None,
              'user': 'user',
              'password': 'pass'})

    def test_setstate(self):
        roles = (object, object)
        server = ProvyServer("foo", "testserver", "user", roles)
        server.__setstate__({
            'name': "  bar  ", 
            "address" : '  foo  ',
            'user': '   user    ',
        })
        self.assertEqual(server.name, 'bar')
        self.assertEqual(server.address, 'foo')
        self.assertEqual(server.username, 'user')


