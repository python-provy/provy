#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Rails applications utility methods for Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole
from provy.more.debian.package.gem import GemRole

class RailsRole(Role):
    '''
    This role provides Rails application utilities for Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import RailsRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(RailsRole) as role:
                role.ensure_site_disabled('default')
                role.create_site(site='my-site', path='/home/myuser/my-site)
                role.ensure_site_enabled('my-site')
    </pre>
    '''

    def __available_site_for(self, name):
        return '/etc/nginx/sites-available/%s' % name

    def __enabled_site_for(self, name):
        return '/etc/nginx/sites-enabled/%s' % name

    def provision(self):
        '''
        Installs Rails dependencies. This method should be called upon if overriden in base classes, or Rails won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import RailsRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(RailsRole) # does not need to be called if using with block.
        </pre>
        '''
        self.register_template_loader('provy.more.debian.web')

        with self.using(AptitudeRole) as role:
            for package in 'build-essential zlib1g-dev libssl-dev libpq-dev subversion libcurl4-openssl-dev libmysqlclient-dev libpcre3-dev libxslt1-dev libperl-dev libgcrypt11-dev libcrypto++-dev'.split():
                role.ensure_package_installed(package)

            role.ensure_package_installed('sqlite3')
            role.ensure_package_installed('libsqlite3-dev')

        with self.using(GemRole) as role:
            role.ensure_package_installed('bundler')
            role.ensure_package_installed('passenger')

        if not self.remote_exists_dir('/etc/nginx'):
            self.ensure_dir('/var/log/nginx', sudo=True)
            self.log("passenger-nginx not found! Installing...")
            self.execute('passenger-install-nginx-module --auto --auto-download --prefix=/etc/nginx', sudo=True, stdout=False)
            self.log("passenger-nginx installed.")

        self.update_file('rails.nginx.conf.template', '/etc/nginx/conf/nginx.conf', sudo=True)
        self.update_file('rails.nginx.init.template', '/etc/init.d/nginx', sudo=True)
        self.change_file_mode('/etc/init.d/nginx', 755)

        self.ensure_dir('/etc/nginx/sites-available', sudo=True)
        self.ensure_dir('/etc/nginx/sites-enabled', sudo=True)
        self.ensure_dir('/etc/nginx/conf.d', sudo=True)

    def cleanup(self):
        '''
        Restarts nginx if any changes have been made.
        There's no need to call this method manually.
        '''
        if 'must-restart-nginx' in self.context and self.context['must-restart-nginx']:
            self.restart()

    def ensure_site_disabled(self, site):
        '''
        Ensures that the specified site is removed from nginx list of enabled sites.
        <em>Parameters</em>
        site - Name of the site to disable.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import RailsRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(RailsRole) as role:
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
        from provy.more.debian import RailsRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(RailsRole) as role:
                    role.ensure_site_enabled('my-site')
        </pre>
        '''

        result = self.remote_symlink(self.__available_site_for(site),
                                     self.__enabled_site_for(site),
                                     sudo=True)
        if result:
            self.log('%s nginx site is enabled!' % site)
            self.ensure_restart()

    def create_site(self, site, host, path, port=80, options={}):
        '''
        Adds a website with the specified template to Nginx list of available sites.
        Warning: Do not forget to call <em>ensure_site_enabled</em> after a call to create_site, or your site won't be enabled.
        <em>Parameters</em>
        site - Name of the site to enable.
        host - Server domain that NGINX should respond by.
        path - Path of the rails app.
        port - Port that NGINX will listen in. Defaults to 80.
        options - Options to pass to the NGINX template.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import RailsRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(RailsRole) as role:
                    role.create_site(site='my-site',
                                     host='localhost www.mysite.com',
                                     port=8888,
                                     path='/home/myuser/my-rails-site')
        </pre>
        '''

        template = "rails-nginx.template"
        options['host'] = host
        options['path'] = path
        result = self.update_file(template,
                                  self.__available_site_for(site),
                                  options=options, sudo=True)

        self.execute('su -l %s -c "cd %s && bundle install --without development test --deployment"' % (self.context['owner'], path), sudo=True, stdout=True)
        if result:
            self.log('Installing gems with bundler')
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
