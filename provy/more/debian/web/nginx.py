#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Nginx web server utility methods for Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class NginxRole(Role):
    '''
    This role provides Nginx web server management utilities for Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import NginxRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(NginxRole) as role:
                role.ensure_conf(conf_template='nginx.conf')
                role.ensure_site_disabled('default')
                role.create_site(site='my-site', template='my-site')
                role.ensure_site_enabled('my-site')
    </pre>
    '''

    def __available_site_for(self, name):
        return '/etc/nginx/sites-available/%s' % name

    def __enabled_site_for(self, name):
        return '/etc/nginx/sites-enabled/%s' % name

    def provision(self):
        '''
        Installs Nginx dependencies. This method should be called upon if overriden in base classes, or Nginx won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import NginxRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(NginxRole) # does not need to be called if using with block.
        </pre>
        '''
        with self.using(AptitudeRole) as role:
            role.ensure_up_to_date()
            role.ensure_package_installed('nginx')

    def cleanup(self):
        '''
        Restarts nginx if any changes have been made.
        There's no need to call this method manually.
        '''
        if 'must-restart-nginx' in self.context and self.context['must-restart-nginx']:
            self.restart()

    def ensure_conf(self, conf_template, options={}, nginx_conf_path='/etc/nginx/nginx.conf'):
        '''
        Ensures that nginx configuration is up-to-date with the specified template.
        <em>Parameters</em>
        conf_template - Name of the template for nginx.conf.
        options - Dictionary of options passed to template. Extends context.
        nginx_conf_path - Path of the nginx configuration file. Defaults to /etc/nginx/nginx.conf.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import NginxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(NginxRole) as role:
                    role.ensure_conf(conf_template='nginx.conf')
        </pre>
        '''

        result = self.update_file(conf_template,
                                  nginx_conf_path,
                                  options=options,
                                  sudo=True)
        if result:
            self.log('nginx conf updated!')
            self.ensure_restart()

    def ensure_site_disabled(self, site):
        '''
        Ensures that the specified site is removed from nginx list of enabled sites.
        <em>Parameters</em>
        site - Name of the site to disable.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import NginxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(NginxRole) as role:
                    role.ensure_site_disabled('default')
        </pre>
        '''
        result = self.remove_file(self.__enabled_site_for(site), sudo=True)
        if result:
            self.log('%s nginx site is disabled!' % site)
            self.ensure_restart()

    def ensure_site_enabled(self, site):
        '''
        Ensures that a symlink is created for the specified site at nginx list of enabled sites from the list of available sites.
        <em>Parameters</em>
        site - Name of the site to enable.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import NginxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(NginxRole) as role:
                    role.ensure_site_enabled('my-site')
        </pre>
        '''

        result = self.remote_symlink(self.__available_site_for(site),
                                     self.__enabled_site_for(site),
                                     sudo=True)
        if result:
            self.log('%s nginx site is enabled!' % site)
            self.ensure_restart()

    def create_site(self, site, template, options={}):
        '''
        Adds a website with the specified template to Nginx list of available sites.
        Warning: Do not forget to call <em>ensure_site_enabled</em> after a call to create_site, or your site won't be enabled.
        <em>Parameters</em>
        site - Name of the site to enable.
        template - Site configuration template.
        options - Options to pass to the template.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import NginxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(NginxRole) as role:
                    role.create_site(site='my-site', template='my-site', options={
                        "user": "me"
                    })
        </pre>
        '''

        result = self.update_file(template,
                                  self.__available_site_for(site),
                                  options=options, sudo=True)
        if result:
            self.log('%s nginx site created!' % site)
            self.ensure_restart()

    def ensure_restart(self):
        '''
        Ensures that nginx gets restarted on cleanup. There's no need to call this method as any changes to nginx will trigger it.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import NginxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(NginxRole) as role:
                    role.ensure_restart()
        </pre>
        '''
        self.context['must-restart-nginx'] = True

    def restart(self):
        '''
        Forcefully restarts nginx.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import NginxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(NginxRole) as role:
                    role.restart()
        </pre>
        '''
        command = '/etc/init.d/nginx restart'
        self.execute(command, sudo=True)
