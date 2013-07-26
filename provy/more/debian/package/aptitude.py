#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision packages installed via the Aptitude package manager for Debian distributions.
'''

from base64 import b64encode
from os.path import join
from datetime import datetime, timedelta
import re
from urlparse import urlparse

from fabric.api import settings
from provy.core import Role


class AptitudeRole(Role):
    '''
    This role provides package management operations with Aptitude within Debian distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    role.ensure_package_installed('nginx')
    '''

    time_format = "%d-%m-%y %H:%M:%S"
    key = 'aptitude-up-to-date'
    aptitude = 'aptitude'

    def provision(self):
        '''
        Installs Aptitude dependencies. This method should be called upon if overriden in base classes, or Aptitude won't work properly in the remote server.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AptitudeRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(AptitudeRole) # does not need to be called if using with block.
        '''

        if not self.is_package_installed('aptitude'):
            self.execute('apt-get install aptitude -y', stdout=False, sudo=True)

        self.ensure_up_to_date()
        self.ensure_package_installed('curl')

    def ensure_gpg_key(self, url):
        '''
        Ensures that the specified gpg key is imported into aptitude.

        :param url: URL of the gpg key file.
        :type url: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AptitudeRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AptitudeRole) as role:
                        role.ensure_gpg_key('http://some.url.com/to/key.gpg')
        '''
        command = "curl %s | apt-key add -" % url
        self.execute(command, stdout=False, sudo=True)

    def has_source(self, source_string):
        '''
        Returns :data:`True` if the specified repository is in aptitude's list of repositories.

        :param source_string: Repository string.
        :type source_string: :class:`str`
        :return: Whether the repository string is present or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AptitudeRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AptitudeRole) as role:
                        if role.has_source('deb http://www.las.ic.unicamp.br/pub/ubuntu/ natty main restricted'):
                            pass
        '''

        result = self.execute('grep -ilR \'^%s\' /etc/apt/sources.list /etc/apt/sources.list.d | wc -l' % source_string, stdout=False, sudo=True)
        return int(result) != 0

    def ensure_aptitude_source(self, source_string):
        '''
        Ensures that the specified repository is in aptitude's list of repositories.

        :param source_string: Repository string.
        :type source_string: :class:`str`
        :return: Whether the repository had to be added or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AptitudeRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AptitudeRole) as role:
                        role.ensure_aptitude_source('deb http://www.las.ic.unicamp.br/pub/ubuntu/ natty main restricted')
        '''
        if self.has_source(source_string):
            return False

        self.log("Aptitude source %s not found! Adding it..." % source_string)

        url = self.__parse_source_string(source_string)['uri']
        domain = urlparse(url).netloc
        source_file = '%s_%s' % (b64encode(source_string)[:12], domain)

        command = 'echo "%s" >> /etc/apt/sources.list.d/%s.list' % (source_string, source_file)
        self.execute(command, stdout=False, sudo=True)
        return True

    def __parse_source_string(self, source_string):
        parts = re.split('\s+', source_string, 3)
        return {'type': parts[0], 'uri': parts[1], 'distribution': parts[2], 'components': parts[3]}

    @property
    def update_date_file(self):
        '''
        Returns the path for the file that contains the last update date to aptitudes's list of packages.

        :return: The path to the file.
        :rtype: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AptitudeRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AptitudeRole) as role:
                        file_path = role.update_date_file
        '''
        return join(self.remote_temp_dir(), 'last_aptitude_update')

    def store_update_date(self):
        '''
        Updates the date in the :meth:`update_date_file`.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AptitudeRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AptitudeRole) as role:
                        role.store_update_date()
        '''
        self.execute('echo "%s" > %s' % (datetime.now().strftime(self.time_format), self.update_date_file), stdout=False)

    def get_last_update_date(self):
        '''
        Returns the date in the :meth:`update_date_file`.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AptitudeRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AptitudeRole) as role:
                        last_update = role.get_last_update_date()
        '''
        if not self.remote_exists(self.update_date_file):
            return None

        date = datetime.strptime(self.read_remote_file(self.update_date_file), self.time_format)
        return date

    def ensure_up_to_date(self):
        '''
        Makes sure aptitude's repository is updated if it hasn't been updated in the last 30 minutes.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AptitudeRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AptitudeRole) as role:
                        role.ensure_up_to_date()
        '''
        last_updated = self.get_last_update_date()
        if not self.key in self.context and (not last_updated or (datetime.now() - last_updated > timedelta(minutes=30))):
            self.force_update()

    def force_update(self):
        '''
        Forces an update to aptitude's repository.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AptitudeRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AptitudeRole) as role:
                        role.force_update()
        '''
        self.log('Updating aptitude sources...')
        self.execute('%s update' % self.aptitude, stdout=False, sudo=True)
        self.store_update_date()
        self.log('Aptitude sources up-to-date')
        self.context[self.key] = True

    def is_package_installed(self, package_name):
        '''
        Returns :data:`True` if the given package is installed via aptitude, :data:`False` otherwise.

        :param package_name: Name of the package to verify.
        :type package_name: :class:`str`
        :return: Whether the package is installed or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AptitudeRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AptitudeRole) as role:
                        if role.is_package_installed('nginx'):
                            pass
        '''

        with settings(warn_only=True):
            return package_name in self.execute("dpkg -l | egrep 'ii[ ]*%s\\b'" % package_name, stdout=False, sudo=True)

    def ensure_package_installed(self, package_name, stdout=False, sudo=True):
        '''
        Ensures that the given package is installed via aptitude.

        :param package_name: Name of the package to install.
        :type package_name: :class:`str`
        :param stdout: Indicates whether install progress should be shown to stdout. Defaults to :data:`False`.
        :type stdout: :class:`bool`
        :param sudo: Indicates whether the package should be installed with the super user. Defaults to :data:`True`.
        :type sudo: :class:`bool`
        :return: Whether the package had to be installed or not.
        :rtype: :class:`bool`
        :raise: :class:`provy.more.debian.PackageNotFound <provy.more.debian.package.aptitude.PackageNotFound>` if the package is not found in the repositories.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AptitudeRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AptitudeRole) as role:
                        role.ensure_package_installed('nginx')
        '''

        if not self.is_package_installed(package_name):
            self.__check_before_install(package_name)
            self.log('%s is not installed (via aptitude)! Installing...' % package_name)
            self.execute('%s install -y %s' % (self.aptitude, package_name), stdout=stdout, sudo=sudo)
            self.log('%s is installed (via aptitude).' % package_name)
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
            from provy.more.debian import AptitudeRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AptitudeRole) as role:
                        role.package_exists('nginx') # True
        '''
        try:
            return bool(self.execute('%s show %s' % (self.aptitude, package), stdout=False))
        except SystemExit:
            return False


class PackageNotFound(Exception):
    '''Should be raised when a package doesn't exist.'''
