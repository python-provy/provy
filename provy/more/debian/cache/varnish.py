#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole

class VarnishRole(Role):

    def provision(self):
        with self.using(AptitudeRole) as role:
            role.ensure_gpg_key("http://repo.varnish-cache.org/debian/GPG-key.txt")
            result = role.ensure_aptitude_source("deb http://repo.varnish-cache.org/ubuntu/ lucid varnish-3.0")
            if result: 
                role.force_update()
            role.ensure_package_installed('varnish')

    def ensure_vcl(self, template, varnish_vcl_path='/etc/varnish/default.vcl', options={}, owner=None):
        result = self.update_file(template, varnish_vcl_path, options=options, sudo=True, owner=owner)
        if result:
            self.log('varnish vcl updated!')
            self.ensure_restart()

    def ensure_conf(self, template, varnish_conf_path='/etc/default/varnish', options={}, owner=None):
        result = self.update_file(template, varnish_conf_path, options=options, sudo=True, owner=owner)
        if result:
            self.log('varnish conf updated!')
            self.ensure_restart()

    def cleanup(self):
        if 'must-restart-varnish' in self.context and self.context['must-restart-varnish']:
            self.restart()

    def ensure_restart(self):
        self.context['must-restart-varnish'] = True

    def restart(self):
        command = '/etc/init.d/varnish restart'
        self.execute(command, sudo=True)
