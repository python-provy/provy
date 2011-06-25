#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role

class AptitudeRole(Role):
    key = 'aptitude-up-to-date'

    def ensure_up_to_date(self, context):
        if not self.key in context:
            self.execute('sudo aptitude update')
            context[self.key] = True

