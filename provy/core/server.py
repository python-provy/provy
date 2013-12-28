# -*- coding: utf-8 -*-
from copy import copy


class ProvyServer(object):

    def __init__(self, name, address, username, roles= tuple(), password=None):
        """
        :param name: Logical name of the server
        :param address: Address of the server
        :param username: Username you log into
        :param roles: List of roles for the server
        :param password: Login password
        """
        super(ProvyServer, self).__init__()
        self.name = name

        self.address = address
        self.roles = list(roles)
        self.username = username
        self.password = password
        self.options = {}
        self.ssh_key = None

    @staticmethod
    def from_dict(name, server_dict):
        d = copy(server_dict)
        d['name'] = name
        s = ProvyServer.__new__(ProvyServer)
        s.__setstate__(d)
        return s

    @property
    def host_string(self):
        return "{}@{}".format(self.username, self.address)

    def __getstate__(self):
        dict =  {
            "name": self.name,
            "address": self.address,
            "roles": self.roles,
            "username": self.username,
            "options": self.options,
            "ssh_key": self.ssh_key
        }
        if self.password is not None:
            dict['password'] = self.password
        return dict

    def __setstate__(self, state):
        self.name = state['name'].strip()
        self.address = state['address'].strip()
        self.roles = state.get("roles", [])
        self.username = state['user'].strip()
        self.password = state.get('password', None)
        self.options = state.get('options', {})
        self.ssh_key = state.get('ssh_key', [])

