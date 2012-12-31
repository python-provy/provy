#!/usr/bin/python
# -*- coding: utf-8 -*-
# flake8: noqa

'''
Roles in this namespace are meant to enable users to install packages using package managers such as Aptitude or Pip in Debian distributions.
'''

from provy.more.debian.package.aptitude import AptitudeRole, PackageNotFound
from provy.more.debian.package.pip import PipRole
from provy.more.debian.package.virtualenv import VirtualenvRole
#from provy.more.debian.package.npm import NPMRole # imported at provy.more.debian.__init__ to avoid circular imports
