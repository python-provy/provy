#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide `Memcached <http://memcached.org/>`_ configuration and execution utilities within Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class MemcachedRole(Role):
    '''
    This role provides utility methods for `Memcached <http://memcached.org/>`_ configuration and execution within Debian distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import Memcached

        class MySampleRole(Role):
            def provision(self):
                with self.using(MemcachedRole) as role:
                    role.ensure_conf(verbose_level=2)
    '''

    def provision(self):
        '''
        Installs `Memcached <http://memcached.org/>`_ and its dependencies.
        This method should be called upon if overriden in base classes, or `Memcached <http://memcached.org/>`_ won't work properly in the remote server.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import MemcachedRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(MemcachedRole) # does not need to be called if using with block.
        '''

        self.register_template_loader('provy.more.debian.cache')

        with self.using(AptitudeRole) as role:
            role.ensure_package_installed('memcached')
            role.ensure_package_installed('libmemcached-dev')

    def ensure_conf(self,
                    owner='root',
                    log_folder='/var/log/memcached',
                    verbose_level=0,
                    memory_in_mb=64,
                    host='127.0.0.1',
                    port=11211,
                    user='nobody',
                    simultaneous_connections=1024,
                    lock_down=False,
                    error_when_memory_exhausted=False,
                    maximize_core_file_limit=False,
                    conf_path='/etc/memcached.conf'
                    ):
        '''
        Ensures that Memcached's configuration file at the specified path is up-to-date.

        :param owner: Owner of the config file. Defaults to root.
        :type owner: :class:`str`
        :param log_folder: Log memcached's output. Defaults to `/var/log/memcached`.
        :type log_folder: :class:`str`
        :param verbose_level: `0` for no verbosity, `1` for verbose, `2` for extra-verbose. Defaults to `0`.
        :type verbose_level: :class:`int`
        :param memory_in_mb: Start with a cap of 64 megs of memory. It's reasonable, and the daemon default.
            Note that the daemon will grow to this size, but does not start out holding this much memory.
        :type memory_in_mb: :class:`int`
        :param host: Specify which IP address to listen on. The default is to listen on all IP addresses.
            This parameter is one of the only security measures that memcached has, so make sure it's listening on a firewalled interface. Defaults to `127.0.0.1`.
        :type host: :class:`str`
        :param port: Default connection port is `11211`.
        :type port: :class:`int`
        :param user: Run the daemon as this user. Defaults to "nobody".
        :type user: :class:`str`
        :param simultaneous_connections: Limit the number of simultaneous incoming connections. The default is `1024`.
        :type simultaneous_connections: :class:`int`
        :param lock_down: Whether it should lock down all paged memory. Consult with the Memcached README and homepage before you do this. Defaults to :data:`False`.
        :type lock_down: :class:`bool`
        :param error_when_memory_exhausted: Whether it should return error when memory is exhausted (rather than removing items). Defaults to :data:`False`.
        :type error_when_memory_exhausted: :class:`bool`
        :param maximize_core_file_limit: Whether it should maximize core file limit. Defaults to :data:`False`.
        :type maximize_core_file_limit: :class:`bool`
        :param conf_path: The path that the configuration file will be in the remote server. Defaults to `/etc/memcached.conf`.
        :type conf_path: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import MemcachedRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(MemcachedRole) as role:
                        role.ensure_conf()
        '''

        options = {
            'log_folder': log_folder.rstrip('/'),
            'verbose_level': verbose_level,
            'memory_in_mb': memory_in_mb,
            'host': host,
            'port': port,
            'user': user,
            'simultaneous_connections': simultaneous_connections,
            'lock_down': lock_down,
            'error_when_memory_exhausted': error_when_memory_exhausted,
            'maximize_core_file_limit': maximize_core_file_limit
        }

        result = self.update_file('memcached.conf.template', conf_path, options=options, owner=self.context['owner'], sudo=True)
        if result:
            self.log('memcached conf updated!')
            self.ensure_restart()

    def cleanup(self):
        '''
        Restarts memcached if it needs to be restarted (any changes made during this server's provisioning).

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import MemcachedRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(MemcachedRole) as role:
                        role.cleanup() # No need to call this if using a with block.
        '''
        if 'must-restart-memcached' in self.context and self.context['must-restart-memcached']:
            self.restart()

    def ensure_restart(self):
        '''
        Ensures that Memcached is restarted on cleanup phase.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import MemcachedRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(MemcachedRole) as role:
                        role.ensure_restart() # No need to call this if using a with block.
        '''
        self.context['must-restart-memcached'] = True

    def restart(self):
        '''
        Forcefully restarts Memcached in the remote server.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import MemcachedRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(MemcachedRole) as role:
                        if not self.is_process_running('memcached'):
                            role.restart()
        '''
        command = '/etc/init.d/memcached restart'
        self.execute(command, sudo=True)
