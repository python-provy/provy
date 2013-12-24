#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide `Ruby on Rails <http://rubyonrails.org/>`_ applications utility methods for Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole
from provy.more.debian.package.gem import GemRole
from provy.more.debian.web.nginx import NginxRole


PACKAGES_TO_INSTALL = (
    'build-essential',
    'zlib1g-dev',
    'libssl-dev',
    'libpq-dev',
    'subversion',
    'libcurl4-openssl-dev',
    'libmysqlclient-dev',
    'libpcre3-dev',
    'libxslt1-dev',
    'libperl-dev',
    'libgcrypt11-dev',
    'libcrypto++-dev',
    'sqlite3',
    'libsqlite3-dev',
)


class RailsRole(Role):
    '''
    This role provides `Ruby on Rails <http://rubyonrails.org/>`_ application utilities for Debian distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import RailsRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(RailsRole) as role:
                    role.ensure_site_disabled('default')
                    role.create_site(site='my-site', path='/home/myuser/my-site')
                    role.ensure_site_enabled('my-site')
    '''

    def __available_site_for(self, name):
        return '/etc/nginx/sites-available/%s' % name

    def provision(self):
        '''
        Installs `Ruby on Rails <http://rubyonrails.org/>`_ dependencies.
        This method should be called upon if overriden in base classes, or Rails won't work properly in the remote server.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import RailsRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(RailsRole) # does not need to be called if using with block.
        '''
        self.register_template_loader('provy.more.debian.web')

        self.__install_system_packages()
        self.__install_gem_packages()
        self.__install_nginx_module()
        self.__create_nginx_configurations()
        self.__create_nginx_directories()

    def __create_nginx_directories(self):
        self.ensure_dir('/etc/nginx/sites-available', sudo=True)
        self.ensure_dir('/etc/nginx/sites-enabled', sudo=True)
        self.ensure_dir('/etc/nginx/conf.d', sudo=True)

    def __create_nginx_configurations(self):
        self.update_file('rails.nginx.conf.template', '/etc/nginx/conf/nginx.conf', sudo=True)
        self.update_file('rails.nginx.init.template', '/etc/init.d/nginx', sudo=True)
        self.change_path_mode('/etc/init.d/nginx', 755)

    def __install_gem_packages(self):
        with self.using(GemRole) as role:
            role.ensure_package_installed('bundler')
            role.ensure_package_installed('passenger')

    def __install_system_packages(self):
        with self.using(AptitudeRole) as role:
            for package in PACKAGES_TO_INSTALL:
                role.ensure_package_installed(package)

    def __install_nginx_module(self):
        if not self.remote_exists_dir('/etc/nginx'):
            self.ensure_dir('/var/log/nginx', sudo=True)
            self.log("passenger-nginx not found! Installing...")
            self.execute('passenger-install-nginx-module --auto --auto-download --prefix=/etc/nginx', sudo=True, stdout=False)
            self.log("passenger-nginx installed.")

    def cleanup(self):
        '''
        Restarts nginx if any changes have been made.

        There's no need to call this method manually.
        '''
        super(RailsRole, self).cleanup()
        if 'must-restart-nginx' in self.context and self.context['must-restart-nginx']:
            self.restart()

    def ensure_site_disabled(self, site):
        '''
        Ensures that the specified site is removed from Nginx list of enabled sites.

        :param site: Name of the site to disable.
        :type site: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import RailsRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(RailsRole) as role:
                        role.ensure_site_disabled('default')
        '''
        with self.using(NginxRole) as nginx:
            nginx.ensure_site_disabled(site)

    def ensure_site_enabled(self, site):
        '''
        Ensures that a symlink is created for the specified site at Nginx list of enabled sites from the list of available sites.

        :param site: Name of the site to enable.
        :type site: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import RailsRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(RailsRole) as role:
                        role.ensure_site_enabled('my-site')
        '''
        with self.using(NginxRole) as nginx:
            nginx.ensure_site_enabled(site)

    def create_site(self, site, host, path, port=80, options={}):
        '''
        Adds a website with the specified template to Nginx list of available sites.

        .. warning::

            Do not forget to call :meth:`ensure_site_enabled` after a call to create_site, or your site won't be enabled.

        :param site: Name of the site to enable.
        :type site: :class:`str`
        :param host: Server domain that Nginx should respond by.
        :type host: :class:`str`
        :param path: Path of the rails app.
        :type path: :class:`str`
        :param port: Port that Nginx will listen in. Defaults to `80`.
        :type port: :class:`int`
        :param options: Options to pass to the Nginx template. Defaults to empty dict (`{}`).
        :type options: :class:`int`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import RailsRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(RailsRole) as role:
                        role.create_site(site='my-site', host='localhost www.mysite.com',
                                         port=8888, path='/home/myuser/my-rails-site')
        '''

        template = "rails-nginx.template"
        options['host'] = host
        options['path'] = path
        result = self.update_file(template,
                                  self.__available_site_for(site),
                                  options=options, sudo=True)

        self.execute('cd %s && bundle install --without development test --deployment' % path, user=self.context['owner'], stdout=True)
        if result:
            self.log('Installing gems with bundler')
            self.log('%s nginx site created!' % site)
            self.ensure_restart()

    def ensure_restart(self):
        '''
        Ensures that Nginx gets restarted on cleanup. There's no need to call this method as any changes to Nginx will trigger it.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import RailsRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(RailsRole) as role:
                        role.ensure_restart()
        '''
        self.context['must-restart-nginx'] = True

    def restart(self):
        '''
        Forcefully restarts nginx.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import RailsRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(RailsRole) as role:
                        role.restart()
        '''
        with self.using(NginxRole) as nginx:
            nginx.restart()
