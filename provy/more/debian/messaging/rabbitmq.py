#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide `RabbitMQ <http://www.rabbitmq.com/>`_ utilities methods within Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole

from fabric.utils import warn


GUEST_USER_WARNING = ('It is advisable to delete the guest user or change the'
                      ' password to something private, particularly if your broker'
                      ' is accessible publicly.')


class RabbitMqRole(Role):
    '''
    This role provides utility methods for `RabbitMQ <http://www.rabbitmq.com/>`_ utilities within Debian distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import RabbitMqRole
        from provy.more.debian import HostNameRole

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
    '''
    def provision(self):
        '''
        Installs `RabbitMQ <http://www.rabbitmq.com/>`_ and dependencies.
        This method should be called upon if overriden in base classes, or RabbitMQ won't work properly in the remote server.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import HgRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(RabbitMqRole)
        '''
        with self.using(AptitudeRole) as role:
            role.ensure_up_to_date()
            role.ensure_package_installed('rabbitmq-server')

        # Start rabbitmq at startup, TODO: add update-rc.d role
        self.execute('update-rc.d rabbitmq-server defaults', stdout=False,
                     sudo=True)
        self.execute('update-rc.d rabbitmq-server enable', stdout=False, sudo=True)

        # Make sure rabbit is running:
        if not self.is_process_running('rabbitmq-server'):
            self.execute(
                'service rabbitmq-server start', stdout=False, sudo=True,
            )

        if self.user_exists('guest'):
            warn(GUEST_USER_WARNING)

    def user_exists(self, username):
        '''
        Checks if the RabbitMQ user exists.

        :param username: Name of the user to be checked.
        :type username: :class:`str`

        :return: Whether the user exists or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(RabbitMqRole) as role:
                        role.user_exists('johndoe')
        '''
        cmd = 'rabbitmqctl list_users'
        users = self.execute(cmd, stdout=False, sudo=True)
        return username in users

    def vhost_exists(self, vhost):
        '''
        Checks if the RabbitMQ vhost exists.

        :param vhost: Name of the vhost to be checked.
        :type vhost: :class:`str`

        :return: Whether the vhost exists or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(RabbitMqRole) as role:
                        role.vhost_exists('foobarhost')
        '''
        vhs = self.execute('rabbitmqctl list_vhosts', stdout=False, sudo=True)
        vhs = vhs.split('\r\n')[1:-1]
        return vhost in vhs

    def ensure_user(self, username, password, is_admin=False):
        '''
        Ensure the given user is created in the database and can authenticate with RabbitMQ.

        :param username: Name of the user to be created.
        :type username: :class:`str`
        :param password: Password that the user will use to authenticate to RabbitMQ.
        :type password: :class:`str`

        :return: Whether the user had to be created or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(RabbitMqRole) as role:
                        role.ensure_user(some_user, some_pass)
        '''
        if not self.user_exists(username):
            self.log('Setting up user %s and password' % username)

            cmd = 'rabbitmqctl add_user %s %s' % (username, password)
            self.execute(cmd, sudo=True)

            if is_admin:
                cmd = 'rabbitmqctl set_user_tags %s administrator' % (username)
                self.execute(cmd, sudo=True)

            self.log('User %s added!' % username)
            return True

        return False

    def delete_user(self, user):
        '''
        Delete user from rabbitmq if exists

        :param user: Name of the user to be deleted.
        :type user: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(RabbitMqRole) as role:
                        role.delete_user('guest', some_pass)
        '''
        if self.user_exists(user):
            self.log('User %s exists, deleting')

            cmd = 'rabbitmqctl delete_user %s' % user
            self.execute(cmd, stdout=False, sudo=True)

            self.log('User %s deleted' % user)

    def ensure_vhost(self, vhost):
        '''
        Ensure the given vhost is created.

        :param vhost: Name of the vhost to be checked/created.
        :type vhost: :class:`str`

        :return: Whether the vhost had to be created or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(RabbitMqRole) as role:
                        role.ensure_vhost('/some_vhost')
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

        :param vhost: Virtual host name to assign the permissions at.
        :type vhost: :class:`str`
        :param username: User to assign permissions to.
        :type username: :class:`str`
        :param perms: Permissions to assign to user (e.g.: '".*" ".*" ".*"').
        :type perms: :class:`str`

        :return: Whether the permissions could be assigned or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(RabbitMqRole) as role:
                        role.ensure_permission(
                            'previous_created_vhost',
                            'previous_created_user',
                            '".*" ".*" ".*"',
                        )
        '''
        if not self.user_exists(username):
            msg = 'Cannot set permission: User %s doesn\'t exist' % username
            self.log(msg)
            return False

        if not self.vhost_exists(vhost):
            self.log('Cannot set permission: vhost %s doesn\'t exist' % vhost)
            return False

        msg = 'Setting up permissions for user %s on vhost %s'
        msg = msg % (username, vhost)
        self.log(msg)

        args = (vhost, username, perms)
        cmd = 'rabbitmqctl set_permissions -p %s %s %s' % args
        self.execute(cmd, stdout=False, sudo=True)

        return True
