#!/usr/bin/python
# -*- coding: utf-8 -*-


def import_module(module_name):
    module = __import__(module_name)
    if '.' in module_name:
        return reduce(getattr, module_name.split()[1:], module)
    return module
