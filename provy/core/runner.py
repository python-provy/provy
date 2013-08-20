#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
This is the internal module responsible for running provy over the provyfile that was provided.

It's recommended not to tinker with this module, as it might prevent your provyfile from working.
'''

from os.path import abspath, dirname, join

from fabric.context_managers import settings as _settings

from provy.core.utils import import_module, AskFor, provyfile_module_from
from provy.core.errors import ConfigurationError
from jinja2 import FileSystemLoader, ChoiceLoader


def run(provfile_path, server_name, password, extra_options):
    module_name = provyfile_module_from(provfile_path)
    prov = import_module(module_name)
    servers = get_servers_for(prov, server_name)

    build_prompt_options(servers, extra_options)

    for server in servers:
        provision_server(server, provfile_path, password, prov)


def print_header(msg):
    print
    print "*" * len(msg)
    print msg
    print "*" * len(msg)


def provision_server(server, provfile_path, password, prov):
    host_string = "%s@%s" % (server['user'], server['address'].strip())

    context = {
        'abspath': dirname(abspath(provfile_path)),
        'path': dirname(provfile_path),
        'owner': server['user'],
        'cleanup': [],
        'registered_loaders': []
    }

    aggregate_node_options(server, context)

    loader = ChoiceLoader([
        FileSystemLoader(join(context['abspath'], 'files'))
    ])
    context['loader'] = loader

    print_header("Provisioning %s..." % host_string)

    settings_dict = dict(host_string=host_string, password=password)
    if 'ssh_key' in server and server['ssh_key']:
        settings_dict['key_filename'] = server['ssh_key']

    with _settings(**settings_dict):
        context['host'] = server['address']
        context['user'] = server['user']
        role_instances = []

        try:
            for role in server['roles']:
                context['role'] = role
                instance = role(prov, context)
                role_instances.append(instance)
                instance.provision()
        finally:
            for role in role_instances:
                role.cleanup()

            for role in context['cleanup']:
                role.cleanup()

    print_header("%s provisioned!" % host_string)


def aggregate_node_options(server, context):
    for key, value in server.get('options', {}).iteritems():
        context[key] = value


def build_prompt_options(servers, extra_options):
    for server in servers:
        for option_name, option in server.get('options', {}).iteritems():
            if isinstance(option, AskFor):
                if option.key in extra_options:
                    value = extra_options[option.key]
                else:
                    value = option.get_value(server)
                server['options'][option_name] = value


def get_servers_for(prov, server_name):
    return get_items(prov, server_name, 'servers', lambda item: isinstance(item, dict) and 'address' in item)


def get_items(prov, item_name, item_key, test_func):
    if not hasattr(prov, item_key):
        raise ConfigurationError('The %s collection was not found in the provyfile file.' % item_key)

    items = getattr(prov, item_key)

    for item_part in item_name.split('.'):
        items = items[item_part]

    found_items = []
    recurse_items(items, test_func, found_items)
    return found_items


def recurse_items(col, test_func, found_items):
    if not isinstance(col, dict):
        return

    if test_func(col):
        found_items.append(col)
    else:
        for key, val in col.iteritems():
            if test_func(val):
                found_items.append(val)
            else:
                recurse_items(val, test_func, found_items)
