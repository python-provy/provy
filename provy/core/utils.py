#!/usr/bin/python
# -*- coding: utf-8 -*-

from getpass import getpass

def import_module(module_name):
    module = __import__(module_name)
    if '.' in module_name:
        return reduce(getattr, module_name.split()[1:], module)
    return module

class AskFor(object):
    def __init__(self, key, question):
        self.key = key
        self.question = question

    def get_value(self, server):
        value = getpass("[Server at %s] - %s: " % (server['address'], self.question))
        return value
