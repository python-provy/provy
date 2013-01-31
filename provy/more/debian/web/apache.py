# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide `Apache HTTP Server <http://httpd.apache.org/>`_ utility methods for Debian distributions.
'''

from fabric.api import settings

from provy.core.roles import Role
from provy.more.debian import AptitudeRole


class ApacheRole(Role):
    '''
    This role provides `Apache HTTP Server <http://httpd.apache.org/>`_ management utilities for Debian distributions.

    Provisions with apache2 as default, that is, it uses the apache2-mpm-worker variant.

    If you want to use the apache2-mpm-prefork variant, just use install this package with :class:`AptitudeRole <provy.more.debian.package.aptitude.AptitudeRole>` and restart Apache.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import ApacheRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(ApacheRole) as role:
                    role.ensure_mod('php5') # Installs and enables mod_php
                    role.ensure_site_disabled('default')
                    role.create_site(site='my-site', template='my-site')
                    role.ensure_site_enabled('my-site')
    '''

    def __available_site_for(self, name):
        return '/etc/apache2/sites-available/%s' % name

    def __enabled_site_for(self, name):
        return '/etc/apache2/sites-enabled/%s' % name

    def __init__(self, prov, context):
        super(ApacheRole, self).__init__(prov, context)
        self.must_restart = False

    def provision(self):
        '''
        Installs `Apache <http://httpd.apache.org/>`_ dependencies. This method should be called upon if overriden in base classes, or Apache won't work properly in the remote server.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import ApacheRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(ApacheRole) # does not need to be called if using with block.
        '''

        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('apache2')

    def cleanup(self):
        '''
        Restarts Apache if any changes have been made.

        There's no need to call this method manually.
        '''
        super(ApacheRole, self).cleanup()
        if self.must_restart:
            self.restart()

    def ensure_mod(self, mod):
        '''
        Installs the module package and enables it in Apache.

        :param mod: Name of the module to enable.
        :type mod: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import ApacheRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(ApacheRole) as role:
                        role.ensure_mod('php5') # Installs "libapache2-mod-php5" and enables it
        '''

        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('libapache2-mod-%s' % mod)

        self.execute('a2enmod %s' % mod, sudo=True)
        self.ensure_restart()

    def create_site(self, site, template, options={}):
        '''
        Adds a website with the specified template to Apache list of available sites.

        .. warning::

            Do not forget to call :meth:`ensure_site_enabled` after a call to create_site, or your site won't be enabled.

        :param site: Name of the site to enable.
        :type site: :class:`str`
        :param template: Site configuration template.
        :type template: :class:`str`
        :param options: Options to pass to the template. Defaults to empty dict (:data:`{}`).
        :type options: :class:`dict`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import ApacheRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(ApacheRole) as role:
                        role.create_site(site='my-site', template='my-site', options={
                            "foo": "bar"
                        })
        '''

        self.update_file(template, self.__available_site_for(site), options=options, sudo=True)
        self.ensure_restart()

    def ensure_site_enabled(self, site):
        '''
        Ensures that a symlink is created for the specified site at the Apache list of enabled sites from the list of available sites.

        :param site: Name of the site to enable.
        :type site: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import ApacheRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(ApacheRole) as role:
                        role.ensure_site_enabled('my-site')
        '''

        with settings(warn_only=True):
            self.remote_symlink(from_file=self.__available_site_for(site), to_file=self.__enabled_site_for(site), sudo=True)
        self.ensure_restart()

    def ensure_site_disabled(self, site):
        '''
        Ensures that the specified site is removed from the Apache list of enabled sites.

        :param site: Name of the site to disable.
        :type site: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import ApacheRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(ApacheRole) as role:
                        role.ensure_site_disabled('default')
        '''

        with settings(warn_only=True):
            self.remove_file(self.__enabled_site_for(site), sudo=True)
        self.ensure_restart()

    def ensure_restart(self):
        '''
        Ensures that Apache gets restarted on cleanup. There's no need to call this method as any changes to Apache will trigger it.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import ApacheRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(ApacheRole) as role:
                        role.ensure_restart()
        '''

        self.must_restart = True

    def restart(self):
        '''
        Forcefully restarts Apache.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import ApacheRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(ApacheRole) as role:
                        role.restart()
        '''

        self.execute('service apache2 restart', sudo=True)
        self.must_restart = False
