#!/usr/bin/python
# -*- coding: utf-8 -*-
# flake8: noqa

'''
Roles in this namespace are meant to provision caching engines, such as `Varnish <https://www.varnish-cache.org/>`_ or `Memcached <http://memcached.org/>`_ in Debian distributions.
'''

from provy.more.debian.cache.varnish import VarnishRole
from provy.more.debian.cache.memcached import MemcachedRole
