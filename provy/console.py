#!/usr/bin/env python
# -*- coding: utf-8 -*-

# provy provisioning
# https://github.com/heynemann/provy

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 Bernardo Heynemann heynemann@gmail.com

import sys
import os
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
    (options, args) = __get_arguments()

    sys.path.insert(0, os.curdir)
    if args:
        provyfile_name = args[0]
    else:
        provyfile_name = 'provyfile.py'

    provyfile_path = __get_provy_file_path(provyfile_name)
    if not provyfile_path:
        provyfile_path = __get_provy_file_path('provy_file.py')

    if not provyfile_path:
        print "The file %s could not be found!" % provyfile_name
        sys.exit(1)
    run(provyfile_path, options.server, options.password)
    sys.exit(0)

if __name__ == '__main__':
    main()
