#!/usr/bin/python
# -*- coding: utf-8 -*-

from fabric.api import run, sudo

class Role(object):
    def __init__(self, prov):
        self.prov = prov

    def provision(self, context):
        pass

    def execute(self, command):
        run(command)

    def sudo_execute(self, command):
        sudo(command)
