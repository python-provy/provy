# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Apache HTTP Server utility methods for Debian distributions.
'''

from fabric.api import settings

from provy.core.roles import Role
from provy.more.debian import AptitudeRole


class ApacheRole(Role):
    '''
    This role provides Apache HTTP Server management utilities for Debian distributions.
    Provisions with apache2 as default, that is, it uses the apache2-mpm-worker variant.
    If you want to use the apache2-mpm-prefork variant, just use install this package with AptitudeRole and restart Apache.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import ApacheRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(ApacheRole) as role:
                role.ensure_mod('php5') # Installs and enables mod_php
                role.ensure_site_disabled('default')
                role.create_site(site='my-site', template='my-site')
                role.ensure_site_enabled('my-site')
    </pre>
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
        Installs Apache dependencies. This method should be called upon if overriden in base classes, or Apache won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import ApacheRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(ApacheRole) # does not need to be called if using with block.
        </pre>
        '''

        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('apache2')

    def cleanup(self):
        '''
        Restarts Apache if any changes have been made.
        There's no need to call this method manually.
        '''
        if self.must_restart:
            self.restart()

    def ensure_mod(self, mod):
        '''
        Installs the module package and enables it in Apache.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import ApacheRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(ApacheRole) as role:
                    role.ensure_mod('php5') # Installs "libapache2-mod-php5" and enables it
        </pre>
        '''

        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('libapache2-mod-%s' % mod)

        self.execute('a2enmod %s' % mod, sudo=True)
        self.ensure_restart()

    def create_site(self, site, template, options={}):
        '''
        Adds a website with the specified template to Apache list of available sites.
        Warning: Do not forget to call <em>ensure_site_enabled</em> after a call to create_site, or your site won't be enabled.
        <em>Parameters</em>
        site - Name of the site to enable.
        template - Site configuration template.
        options - Options to pass to the template. Defaults to empty dict ({}).
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import ApacheRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(ApacheRole) as role:
                    role.create_site(site='my-site', template='my-site', options={
                        "foo": "bar"
                    })
        </pre>
        '''

        self.update_file(template, self.__available_site_for(site), options=options, sudo=True)
        self.ensure_restart()

    def ensure_site_enabled(self, site):
        '''
        Ensures that a symlink is created for the specified site at the Apache list of enabled sites from the list of available sites.
        <em>Parameters</em>
        site - Name of the site to enable.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import ApacheRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(ApacheRole) as role:
                    role.ensure_site_enabled('my-site')
        </pre>
        '''

        with settings(warn_only=True):
            self.remote_symlink(from_file=self.__available_site_for(site), to_file=self.__enabled_site_for(site), sudo=True)
        self.ensure_restart()

    def ensure_site_disabled(self, site):
        '''
        Ensures that the specified site is removed from the Apache list of enabled sites.
        <em>Parameters</em>
        site - Name of the site to disable.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import ApacheRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(ApacheRole) as role:
                    role.ensure_site_disabled('default')
        </pre>
        '''

        with settings(warn_only=True):
            self.remove_file(self.__enabled_site_for(site), sudo=True)
        self.ensure_restart()

    def ensure_restart(self):
        '''
        Ensures that Apache gets restarted on cleanup. There's no need to call this method as any changes to Apache will trigger it.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import ApacheRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(ApacheRole) as role:
                    role.ensure_restart()
        </pre>
        '''

        self.must_restart = True

    def restart(self):
        '''
        Forcefully restarts Apache.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import ApacheRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(ApacheRole) as role:
                    role.restart()
        </pre>
        '''

        self.execute('service apache2 restart', sudo=True)
        self.must_restart = False

