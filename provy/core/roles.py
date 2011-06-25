#!/usr/bin/python
# -*- coding: utf-8 -*-

from fabric.api import run

class Role(object):
    def __init__(self, prov):
        self.prov = prov

    def provision(self, context):
        pass

    def execute(self, command):
        run(command)
