#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision packages installed via the Yum package manager for CentOS distributions.
'''

from os.path import join
from datetime import datetime, timedelta

from provy.core import Role


class YumRole(Role):
    '''
    This role provides package management operations with Yum within CentOS distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.centos import YumRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(YumRole) as role:
                    role.ensure_package_installed('nginx')
    '''

    time_format = "%d-%m-%y %H:%M:%S"
    key = 'yum-up-to-date'

    def provision(self):
        '''
        Installs Yum dependencies. This method should be called upon if overriden in base classes, or Yum won't work properly in the remote server.

        Example:
        ::

            from provy.core import Role
            from provy.more.centos import YumRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(YumRole) # does not need to be called if using with block.
        '''
        self.ensure_up_to_date()
        self.ensure_package_installed('curl')

    def ensure_gpg_key(self, url):
        '''
        Ensures that the specified gpg key is imported into rpm.

        :param url: URL of the gpg key file.
        :type url: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.centos import YumRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(YumRole) as role:
                        role.ensure_gpg_key('http://some.url.com/to/key.gpg')
        '''
        command = "curl %s | rpm --import -" % url
        self.execute(command, stdout=False, sudo=True)

    def has_source(self, source_string):
        '''
        Ensures that the specified repository is in yum's list of repositories.

        :param source_string: Repository string.
        :type source_string: :class:`str`

        :return: Whether the repository is already configured or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.centos import YumRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(YumRole) as role:
                        if role.has_source('some-path-to-a-repo'):
                            pass
        '''
        return source_string in self.execute('cat /etc/yum.repos.d/CentOS-Base.repo', stdout=False, sudo=True)

    def ensure_yum_source(self, source_string):
        '''
        Ensures that the specified repository is in yum's list of repositories.

        :param source_string: Repository string.
        :type source_string: :class:`str`

        :return: Whether the repository had to be added or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.centos import YumRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(YumRole) as role:
                        role.ensure_yum_source('some-path-to-a-repo')
        '''
        if self.has_source(source_string):
            return False

        self.log("Yum source %s not found! Adding it..." % source_string)
        command = 'echo "%s" >> /etc/yum.repos.d/CentOS-Base.repo' % source_string
        self.execute(command, stdout=False, sudo=True)
        return True

    @property
    def update_date_file(self):
        '''
        Returns the path for the file that contains the last update date to yum's list of packages.

        Example:
        ::

            from provy.core import Role
            from provy.more.centos import YumRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(YumRole) as role:
                        file_path = role.update_date_file
        '''
        return join(self.remote_temp_dir(), 'last_yum_update')

    def store_update_date(self):
        '''
        Updates the date in the :meth:`update_date_file`.

        Example:
        ::

            from provy.core import Role
            from provy.more.centos import YumRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(YumRole) as role:
                        role.store_update_date()
        '''

        self.execute('echo "%s" > %s' % (datetime.now().strftime(self.time_format), self.update_date_file), stdout=False)

    def get_last_update_date(self):
        '''
        Returns the date in the :meth:`update_date_file`.

        Example:
        ::

            from provy.core import Role
            from provy.more.centos import YumRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(YumRole) as role:
                        last_update = role.get_last_update_date()
        '''
        if not self.remote_exists(self.update_date_file):
            return None

        date = datetime.strptime(self.read_remote_file(self.update_date_file), self.time_format)
        return date

    def ensure_up_to_date(self):
        '''
        Makes sure Yum's repository is updated if it hasn't been updated in the last 30 minutes.

        Example:
        ::

            from provy.core import Role
            from provy.more.centos import YumRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(YumRole) as role:
                        role.ensure_up_to_date()
        '''

        last_updated = self.get_last_update_date()
        if not self.key in self.context and (not last_updated or (datetime.now() - last_updated > timedelta(minutes=30))):
            self.force_update()

    def force_update(self):
        '''
        Forces an update to Yum's repository.

        Example:
        ::

            from provy.core import Role
            from provy.more.centos import YumRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(YumRole) as role:
                        role.force_update()
        '''
        self.log('Updating yum sources...')
        self.execute('yum clean all', stdout=False, sudo=True)
        self.store_update_date()
        self.log('Yum sources up-to-date')
        self.context[self.key] = True

    def is_package_installed(self, package_name):
        '''
        Returns :data:`True` if the given package is installed via Yum, :data:`False` otherwise.

        :param package_name: The name of the package to check.
        :type package_name: :class:`str`

        :return: Whether the package is installed or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.centos import YumRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(YumRole) as role:
                        if role.is_package_installed('nginx'):
                            pass
        '''
        package = self.execute(
            'rpm -qa %s' % package_name, stdout=False, sudo=True,
        )
        return bool(package)

    def ensure_package_installed(self, package_name):
        '''
        Ensures that the given package is installed via Yum.

        :param package_name: The name of the package to install.
        :type package_name: :class:`str`

        :return: Whether the package had to be installed or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.centos import YumRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(YumRole) as role:
                        role.ensure_package_installed('nginx')
        '''
        if not self.is_package_installed(package_name):
            self.__check_before_install(package_name)
            self.log('%s is not installed (via yum)! Installing...' % package_name)
            self.execute('yum install -y %s' % package_name, stdout=False, sudo=True)
            self.log('%s is installed (via yum).' % package_name)
            return True
        return False

    def __check_before_install(self, package_name):
        if not self.package_exists(package_name):
            raise PackageNotFound('Package "%s" not found in repositories' % package_name)

    def package_exists(self, package):
        '''
        Checks if the given package exists.

        :param package: Name of the package to check.
        :type package: :class:`str`
        :return: Whether the package exists or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.centos import YumRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(YumRole) as role:
                        role.package_exists('nginx') # True
        '''
        try:
            return bool(self.execute('yum info -q %s' % package, stdout=False))
        except SystemExit:
            return False


class PackageNotFound(Exception):
    '''Should be raised when a package doesn't exist.'''
