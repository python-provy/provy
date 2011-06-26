#!/usr/bin/python
# -*- coding: utf-8 -*-


from provy.more.debian.package.aptitude import AptitudeRole

class NginxRole(AptitudeRole):
    def available_site_for(self, name):
        return '/etc/nginx/sites-available/%s' % name

    def enabled_site_for(self, name):
        return '/etc/nginx/sites-enabled/%s' % name

    def provision(self):
        self.ensure_up_to_date()
        self.ensure_package_installed('nginx')

    def cleanup(self):
        if 'must-restart-nginx' in self.context and self.context['must-restart-nginx']:
            self.restart()

    def ensure_conf(self, conf_template, options, nginx_conf_path='/etc/nginx/nginx.conf'):
        self.log('Ensuring nginx conf is up-to-date...')
        result = self.update_file(self.local_file(conf_template), nginx_conf_path, options=options, sudo=True)
        self.log('nginx conf up-to-date!')
        if result:
            self.ensure_restart()

    def ensure_site_disabled(self, site):
        self.log('Ensuring nginx site %s is disabled...' % site)
        result = self.remove_file(self.enabled_site_for(site), sudo=True)
        self.log('%s nginx site is disabled!' % site)
        if result:
            self.ensure_restart()

    def ensure_site_enabled(self, site):
        self.log('Ensuring nginx site %s is enabled...' % site)
        result = self.remote_symlink(self.available_site_for(site), self.enabled_site_for(site), sudo=True)
        self.log('%s nginx site is enabled!' % site)
        if result:
            self.ensure_restart()

    def create_site(self, site, template, options):
        self.log('Creating nginx site %s from template %s' % (site, template))
        result = self.update_file(self.local_file(template), self.available_site_for(site), options, sudo=True)
        self.log('%s nginx site created!' % site)
        if result:
            self.ensure_restart()

    def ensure_restart(self):
        self.context['must-restart-nginx'] = True

    def restart(self):
        command = '/etc/init.d/nginx restart'
        self.execute(command, sudo=True)
