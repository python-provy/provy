#!/usr/bin/env python
# -*- coding: utf-8 -*-

# provy provisioning
# https://github.com/heynemann/provy

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 Bernardo Heynemann heynemann@gmail.com

import sys
import os
import re
from os.path import exists, abspath, splitext
from optparse import OptionParser

from provy.core import run


class Messages(object):
    role = """Role to provision the specified servers with. This is a recursive
    option"""
    server = """Servers to provision with the specified role. This is a
    recursive option."""
    password = """Password to use for authentication with servers.
    If passwords differ from server to server this does not work."""


def __get_extra_options():
    extra_options = {}
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            match = re.match('(?P<key>.+?)=(?P<value>.+)', arg)
            if match:
                extra_options[match.groupdict()['key']] = match.groupdict()['value']
                sys.argv.remove(arg)

    return extra_options


def __get_arguments():
    parser = OptionParser()
    parser.add_option("-s", "--server", dest="server", help=Messages.server)
    parser.add_option("-p", "--password", dest="password", default=None,
                      help=Messages.password)

    (options, args) = parser.parse_args()

    return (options, args)


def __get_provy_file_path(provyfile_name):
    path = abspath(provyfile_name)
    if not exists(path):
        return None
    return splitext(path.replace(abspath('.'), '').lstrip('/').rstrip('/'))[0]


def main():
    extra_options = __get_extra_options()
    (options, args) = __get_arguments()

    sys.path.insert(0, os.curdir)
    if args:
        provyfile_name = args[0]
    else:
        provyfile_name = 'provyfile.py'

    provyfile_path = __get_provy_file_path(provyfile_name)
    if not provyfile_path:
        provyfile_path = __get_provy_file_path('provy_file.py')

    if options.server is None and provyfile_path:
        # TODO: Improve this code to 'find' the set of servers defined in the
        # provyfile and run with the defined server set (if only one is defined)
        print "\nInfo: Provy is running using the 'test' set of servers.\n"
        options.server = 'test'

    if not provyfile_path:
        print "The file %s could not be found!" % provyfile_name
        sys.exit(1)
    run(provyfile_path, options.server, options.password, extra_options)
    sys.exit(0)

if __name__ == '__main__':
    main()
