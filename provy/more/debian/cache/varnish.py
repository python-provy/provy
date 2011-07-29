#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Varnish configuration and execution utilities within Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class VarnishRole(Role):
    '''
    This role provides utility methods for Varnish configuration and execution within Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import VarnishRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(VarnishRole) as role:
                role.ensure_vcl('default.vcl', owner='user')
                role.ensure_conf('default_varnish', owner='user')
    </pre>
    '''

    def provision(self):
        '''
        Installs Varnish and its dependencies. This method should be called upon if overriden in base classes, or Varnish won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import VarnishRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(VarnishRole) # does not need to be called if using with block.
        </pre>
        '''

        with self.using(AptitudeRole) as role:
            role.ensure_gpg_key("http://repo.varnish-cache.org/debian/GPG-key.txt")
            result = role.ensure_aptitude_source("deb http://repo.varnish-cache.org/ubuntu/ lucid varnish-3.0")
            if result:
                role.force_update()
            role.ensure_package_installed('varnish')

    def ensure_vcl(self, template, varnish_vcl_path='/etc/varnish/default.vcl', options={}, owner=None):
        '''
        Ensures that the VCL file at the specified path is up-to-date.
        <em>Parameters</em>
        template - The name of the VCL template file.
        varnish_vcl_path - The path that the VCL file will be in the remote server. Defaults to /etc/varnish/default.vcl.
        options - Dictionary of options to pass to the VCL template file. Extends context.
        owner - Owner of the VCL file at the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import VarnishRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(VarnishRole) as role:
                    role.ensure_vcl('default.vcl', owner='user')
        </pre>
        '''

        result = self.update_file(template, varnish_vcl_path, options=options, sudo=True, owner=owner)
        if result:
            self.log('varnish vcl updated!')
            self.ensure_restart()

    def ensure_conf(self, template, varnish_conf_path='/etc/default/varnish', options={}, owner=None):
        '''
        Ensures that Varnish's configuration file at the specified path is up-to-date.
        <em>Parameters</em>
        template - The name of the VCL template file.
        varnish_conf_path - The path that the configuration file will be in the remote server. Defaults to /etc/default/varnish.
        options - Dictionary of options to pass to the configuration template file. Extends context.
        owner - Owner of the configuration file at the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import VarnishRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(VarnishRole) as role:
                    role.ensure_conf('default_varnish', owner='user')
        </pre>
        '''

        result = self.update_file(template, varnish_conf_path, options=options, sudo=True, owner=owner)
        if result:
            self.log('varnish conf updated!')
            self.ensure_restart()

    def cleanup(self):
        '''
        Restarts Varnish if it needs to be restarted (any changes made during this server's provisioning).
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import VarnishRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(VarnishRole) as role:
                    role.cleanup() # No need to call this if using a with block.
        </pre>
        '''
        if 'must-restart-varnish' in self.context and self.context['must-restart-varnish']:
            self.restart()

    def ensure_restart(self):
        '''
        Ensures that Varnish is restarted on cleanup phase.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import VarnishRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(VarnishRole) as role:
                    role.ensure_restart() # No need to call this if using a with block.
        </pre>
        '''
        self.context['must-restart-varnish'] = True

    def restart(self):
        '''
        Forcefully restarts Varnish in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import VarnishRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(VarnishRole) as role:
                    if not self.is_process_running('varnishd'):
                        role.restart()
        </pre>
        '''
        command = 'START=yes /etc/init.d/varnish restart'
        self.execute(command, sudo=True)
