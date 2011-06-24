#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.providers.aptitude import AptProvider

class ProviderList(object):
    APT = AptProvider

providers = ProviderList()
