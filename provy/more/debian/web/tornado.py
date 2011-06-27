#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole
from provy.more.debian.package.pip import PipRole

class TornadoRole(Role):
    def provision(self):
        with self.using(AptitudeRole) as role:
            role.ensure_up_to_date()
            role.ensure_package_installed('python-pycurl')

        with self.using(PipRole) as role:
            role.ensure_package_installed('tornado')
