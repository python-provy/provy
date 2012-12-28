#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role, AskFor


provisions = []
cleanups = []
contexts = {}


class Role1(Role):
    def provision(self):
        provisions.append(self.__class__)
        contexts[self.__class__] = self.context
        self.context['cleanup'].extend([
            Role2(self.prov, self.context),
            Role3(self.prov, self.context),
        ])

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


class Role4(Role):
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
                'password': AskFor('password', 'Provide a password'),
                'another-password': AskFor('another-password', 'Provide another password'),
            },
            'ssh_key': '/some/key.pub',
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
            },
        },
    },
    'test2': {
        'address': '33.33.33.35',
        'user': 'vagrant',
        'roles': [
            Role4,
        ],
        'options': {
            'foo': 'FOO',
        },
    },
}
