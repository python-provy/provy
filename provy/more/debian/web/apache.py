# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Apache HTTP Server utility methods for Debian distributions.
'''

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
                role.create_site(site='my-site', template='my-site')
    </pre>
    '''

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

        available = '/etc/apache2/sites-available/%s' % site
        enabled = '/etc/apache2/sites-enabled/%s' % site

        self.update_file(template, available, options=options, sudo=True)
        self.remote_symlink(from_file=available, to_file=enabled, sudo=True)
        self.execute('service apache2 restart', sudo=True)
