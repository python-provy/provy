#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision caching engines, such as Varnish or Memcached in Debian distributions.
'''

from provy.more.debian.cache.varnish import VarnishRole
from provy.more.debian.cache.memcached import MemcachedRole
