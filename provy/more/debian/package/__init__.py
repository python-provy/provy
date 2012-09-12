#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to enable users to install packages using package managers such as Aptitude or Pip in Debian distributions.
'''

from provy.more.debian.package.aptitude import AptitudeRole, PackageNotFound
from provy.more.debian.package.pip import PipRole
from provy.more.debian.package.virtualenv import VirtualenvRole
