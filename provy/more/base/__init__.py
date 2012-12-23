#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are base roles which contain common behavior among
distribuitions.
Since them are base classes, they are not suited for provisioning, instead,
you should have a subclass that implements provision method.
'''

from provy.more.base.database import *

