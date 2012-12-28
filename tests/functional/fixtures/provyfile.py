#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role


provisions = []
cleanups = []
contexts = {}


class Role1(Role):
    def provision(self):
        provisions.append(self.__class__)
        contexts[self.__class__] = self.context

    def cleanup(self):
        cleanups.append(self.__class__)


class Role2(Role):
    def provision(self):
        provisions.append(self.__class__)
        contexts[self.__class__] = self.context

    def cleanup(self):
        cleanups.append(self.__class__)


class Role3(Role):
    def provision(self):
        provisions.append(self.__class__)
        contexts[self.__class__] = self.context

    def cleanup(self):
        cleanups.append(self.__class__)

servers = {
    'test': {
        'role1': {
            'address': '33.33.33.33',
            'user': 'vagrant',
            'roles': [
                Role1,
            ],
            'options': {
                'foo': 'FOO',
            }
        },
        'roles2and3': {
            'address': '33.33.33.34',
            'user': 'vagrant',
            'roles': [
                Role2,
                Role3,
            ],
            'options': {
                'bar': 'BAR',
                'baz': 'BAZ',
            }

        }
    }
}
