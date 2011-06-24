#!/usr/bin/env python
# -*- coding: utf-8 -*-

# provy provisioning
# https://github.com/heynemann/provy

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 Bernardo Heynemann heynemann@gmail.com

from os.path import exists, abspath
from optparse import OptionParser

from provy import run

class Messages(object):
    role = """Role to provision the specified servers with. This is a recursive
    option"""
    server = """Servers to provision with the specified role. This is a recursive
    option."""

def __get_arguments():
    parser = OptionParser()
    parser.add_option("-r", "--role", dest="role", help=Messages.role)
    parser.add_option("-s", "--server", dest="server", help=Messages.server)

    (options, args) = parser.parse_args()

    return (options, args)

def __get_provy_file_path():
    path = abspath('provyfile.py')
    if not exists(path):
        path = abspath('provy_file.py')
        if not exists(path):
            return None
    return path

def main():
    (options, args) = __get_arguments()

    provyfile_path = __get_provy_file_path()

    run(provyfile_path, options.role, options.server)

if __name__ == '__main__':
    main()
