#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Rabbitmq utilities methods within
CentOS distributions.
'''

from provy.core import Role
from provy.more.centos.package.yum import YumRole

from fabric.utils import warn


class RabbitMqRole(Role):
    '''
    This role provides utility methods for Rabbitmq utilities
    within CentOS distributions.

    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.centos import RabbitMqRole
    from provy.more.centos import HostNameRole

    class MySampleRole(Role):
        def provision(self):

            with self.using(HostNameRole) as role:
                # From rabbitmq docs [1]:
                # "RabbitMQ names the database directory using the current
                # hostname of the system. If the hostname changes, a new empty
                # database is created.  To avoid data loss it's crucial to set
                # up a fixed and resolvable hostname"
                #
                # [1] http://www.rabbitmq.com/ec2.html

                role.ensure_hostname('rabbit')

            with self.using(RabbitMqRole) as role:
                role.delete_user('guest')
                role.ensure_user(
                    self.context['rabbit_user'],
                    self.context['rabbit_password'],
                )
                role.ensure_vhost(self.context['rabbit_vhost'])
                role.ensure_permission(
                    self.context['rabbit_vhost'],
                    self.context['rabbit_user'],
                    '".*" ".*" ".*"',
                )
    </pre>
    '''
    def provision(self):
        '''
        Installs Rabbitmq and dependencies. This method should be called upon
        if overriden in base classes, or Rabbitmq won't work properly in the
        remote server.

        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import HgRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(RabbitMqRole)
        </pre>
        '''
        with self.using(YumRole) as role:
            role.ensure_up_to_date()
            role.ensure_package_installed('rabbitmq-server')

        # Start rabbitmq at startup, TODO: add chkconfig role
        self.execute('chkconfig --add rabbitmq-server', stdout=False,
                      sudo=True)
        self.execute('chkconfig rabbitmq-server on', stdout=False, sudo=True)

        # Make sure rabbit is running:
        if not self.is_process_running('rabbitmq-server'):
            self.execute(
                'service rabbitmq-server start', stdout=False, sudo=True,
            )

        if self.user_exists('guest'):
            warn('It is advisable to delete the guest user or change the'
                 ' password to something private, particularly if your broker'
                 ' is accessible publicly.')

    def user_exists(self, username):
        cmd = 'rabbitmqctl list_users'
        users = self.execute(cmd, stdout=False, sudo=True)
        return username in users

    def vhost_exists(self, vhost):
        vhs = self.execute('rabbitmqctl list_vhosts', stdout=False, sudo=True)
        vhs = vhs.split('\r\n')[1:-1]
        return vhost in vhs

    def ensure_user(self, username, password):
        '''
        Ensure the given user is created in the database and can authenticate
        with rabbitmq
        <em>Parameters</em>
        username - name of the user to be created.
        password - password that the user will use to authenticate to rabbitmq
        <em>Sample usage</em>
        <pre class="sh_python">
        class MySampleRole(Role):
            def provision(self):
                with self.using(RabbitMqRole) as role:
                    role.ensure_user(some_user, some_pass)
        </pre>
        '''
        if not self.user_exists(username):
            self.log('Setting up user %s and password' % username)

            cmd = 'rabbitmqctl add_user %s %s' % (username, password)
            self.execute(cmd, sudo=True)

            self.log('User %s added!' % username)
            return True

        return False

    def delete_user(self, user):
        '''
        Delete user from rabbitmq if exists
        <em>Parameters</em>
        user - name of user to be deleted
        <em>Sample usage</em>
        <pre class="sh_python">
        class MySampleRole(Role):
            def provision(self):
                with self.using(RabbitMqRole) as role:
                    role.delete_user('guest', some_pass)
        </pre>
        '''
        if self.user_exists(user):
            self.log('User %s exists, deleting')

            cmd = 'rabbitmqctl delete_user %s' % user
            self.execute(cmd, stdout=False, sudo=True)

            self.log('User %s deleted' % user)

    def ensure_vhost(self, vhost):
        '''
        Ensure the given vhost is created.
        <em>Parameters</em>
        vhost - vhost name
        <em>Sample usage</em>
        <pre class="sh_python">
        class MySampleRole(Role):
            def provision(self):
                with self.using(RabbitMqRole) as role:
                    role.ensure_vhost('/some_vhost')
        </pre>
        '''
        if not self.vhost_exists(vhost):
            self.log('Adding vhost %s' % vhost)

            self.execute('rabbitmqctl add_vhost %s' % vhost, sudo=True)

            self.log('vhost %s added!' % vhost)
            return True
        return False

    def ensure_permission(self, vhost, username, perms):
        '''
        Ensure the given user has the given permissions on the specified vhost
        <em>Parameters</em>
        vhost - virtual host name
        username - User to ensure permissions
        perms - Permissions to assign to user (i.e.: '".*" ".*" ".*"')
        <em>Sample usage</em>
        <pre class="sh_python">
        class MySampleRole(Role):
            def provision(self):
                with self.using(RabbitMqRole) as role:
                    role.ensure_permission(
                        'previous_created_vhost',
                        'previous_created_user',
                        '".*" ".*" ".*"',
                    )
        </pre>
        '''
        if not self.user_exists(username):
            msg = 'Cannot set permission: User %s doesn\'t exists' % username
            self.log(msg)
            return False

        if not self.vhost_exists(vhost):
            self.log('Cannot set permission: vhost %s doesn\'t exists' % vhost)
            return False

        msg = 'Setting up permissions for user %s on vhost %s'
        msg = msg % (username, vhost)
        self.log(msg)

        args = (vhost, username, perms)
        cmd = 'rabbitmqctl set_permissions -p %s %s %s' % args
        self.execute(cmd, stdout=False, sudo=True)

        return True
