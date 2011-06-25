#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.more.debian.package.aptitude import AptitudeRole

class NginxRole(AptitudeRole):
    def provision(self, context):
        self.ensure_package_installed('nginx')

