#!/usr/bin/python
# -*- coding: utf-8 -*-

from fabric.context_managers import settings as _settings

from provy.core.utils import import_module
from provy.core.errors import ConfigurationError

def run(provfile_path, role_name, server_name):
    prov = import_module(provfile_path)
    roles = get_roles_for(prov, role_name)
    servers = get_servers_for(prov, server_name)
    context = {}

    for server in servers:
        with _settings(
            host_string="%s@%s" % (server['user'], server['address'])
        ):
            context['host'] = server['address']
            context['user'] = server['user']
            for role in roles:
                context['role'] = role
                role(prov).provision(context)

def get_roles_for(prov, role_name):
    return get_items(prov, role_name, 'roles', lambda item: isinstance(item, (list, tuple)))

def get_servers_for(prov, server_name):
    return get_items(prov, server_name, 'servers', lambda item: isinstance(item, dict) and 'address' in item, recursive=True)

def get_items(prov, item_name, item_key, test_func, recursive=False):
    if not hasattr(prov, item_key):
        raise ConfigurationError('The %s collection was not found in the provyfile file.' % item_key)

    items = getattr(prov, item_key)
    for item_part in item_name.split('.'):
        items = items[item_part]

    if not recursive:
        return items

    found_items = []
    recurse_items(items, test_func, found_items)
    return found_items

def recurse_items(col, test_func, found_items):
    if not isinstance(col, dict):
        return

    for key, val in col.iteritems():
        if test_func(val):
            found_items.append(val)
        else:
            recurse_items(val, test_func, found_items)

