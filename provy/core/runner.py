#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
This is the internal module responsible for running provy over the provyfile that was provided.

It's recommended not to tinker with this module, as it might prevent your provyfile from working.
'''
from copy import copy

from os.path import abspath, dirname, join

from fabric.context_managers import settings as _settings

from provy.core.utils import import_module, AskFor, provyfile_module_from
from provy.core.errors import ConfigurationError
from jinja2 import FileSystemLoader, ChoiceLoader

from .server import ProvyServer


def run(provfile_path, server_name, password, extra_options):
    module_name = provyfile_module_from(provfile_path)
    prov = import_module(module_name)
    servers = get_servers_for(prov, server_name)

    build_prompt_options(servers, extra_options)

    for server in servers:
        provision_server(server, provfile_path, prov)


def print_header(msg):
    print()
    print("*" * len(msg))
    print(msg)
    print("*" * len(msg))


def provision_server(server, provfile_path, prov):
    context = {
        'abspath': dirname(abspath(provfile_path)),
        'path': dirname(provfile_path),
        'owner': server.username,
        'cleanup': [],
        'registered_loaders': [],
        '__provy': {
            'current_server': server
        }
    }

    aggregate_node_options(server, context)

    loader = ChoiceLoader([
        FileSystemLoader(join(context['abspath'], 'files'))
    ])
    context['loader'] = loader

    print_header("Provisioning %s..." % server.host_string)

    settings_dict = dict(host_string=server.host_string, password=server.password)
    if server.ssh_key is not None:
        settings_dict['key_filename'] = server.ssh_key

    with _settings(**settings_dict):
        context['host'] = server.address
        context['user'] = server.username
        role_instances = []

        try:
            for role in server.roles:
                context['role'] = role
                instance = role(prov, context)
                role_instances.append(instance)
                instance.provision()
        finally:
            for role in role_instances:
                role.cleanup()

            for role in context['cleanup']:
                role.cleanup()

    print_header("%s provisioned!" % server.host_string)


def aggregate_node_options(server, context):
    for key, value in server.options.iteritems():
        context[key] = value


def build_prompt_options(servers, extra_options):
    for server in servers:
        for option_name, option in server.options.iteritems():
            if isinstance(option, AskFor):
                if option.key in extra_options:
                    value = extra_options[option.key]
                else:
                    value = option.get_value(server)
                server.options[option_name] = value


def get_servers_for(prov, server_name):
    result = []
    for name, server in  get_items(prov, server_name, 'servers', lambda item: isinstance(item, dict) and 'address' in item):
        result.append(ProvyServer.from_dict(name, server))
    return result

def get_items(prov, item_name, item_key, test_func):
    if not hasattr(prov, item_key):
        raise ConfigurationError('The %s collection was not found in the provyfile file.' % item_key)

    items = getattr(prov, item_key)

    key = None

    for item_part in item_name.split('.'):
        key = item_part
        items = items[item_part]

    found_items = []
    recurse_items(items, test_func, found_items, key)
    return found_items


def recurse_items(col, test_func, found_items, key=None):
    if not isinstance(col, dict):
        return

    if test_func(col):
        found_items.append([key, col])
    else:
        for key, val in col.iteritems():
            if test_func(val):
                found_items.append([key, val])
            else:
                recurse_items(val, test_func, found_items)
