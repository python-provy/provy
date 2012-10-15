#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision packages installed via the Aptitude package manager for Debian distributions.
'''
from contextlib import contextmanager

from os.path import join
from datetime import datetime, timedelta
import re
from fabric.api import settings
from provy.core import Role
from provy.core.errors import ConfigurationError


class AptitudeRole(Role):
    '''
    This role provides package management operations with Aptitude within Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import AptitudeRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(AptitudeRole) as role:
                role.ensure_package_installed('nginx')
    </pre>
    '''

    time_format = "%d-%m-%y %H:%M:%S"
    key = 'aptitude-up-to-date'
    aptitude = 'aptitude'

    @classmethod
    def disable_provision(cls, role):
        """
            Used to temporalily disable AptitudeRole.provision (Why one could want to do it: provision tries to
            download curl, which depending on sources config might not work. Since overriding sources list also uses
            this role).

            Example usage::

                class PrepareApt(Role):
                    def provision(self):
                        super(PrepareApt, self).provision()
                        with AptitudeRole.disable_provision(self):
                            with self.using(AptitudeRole) as role:
                                role.override_sources_list(StringIO(SOURCES_LIST))

            It can be nested.
        """
        @contextmanager
        def manage_context(role):
            role.context['aptitude_no_provision'] = role.context.get('aptitude_no_provision', 0) + 1
            yield
            if role.context['aptitude_no_provision'] == 1:
                del role.context['aptitude_no_provision']
            else:
                role.context['aptitude_no_provision']-=1


        return manage_context(role)

    def provision(self):
        '''
        Installs Aptitude dependencies. This method should be called upon if overriden in base classes, or Aptitude won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(AptitudeRole) # does not need to be called if using with block.
        </pre>
        '''

        if  not self.context.get('aptitude_no_provision', False):
            if not self.is_package_installed('aptitude'):
                self.execute('apt-get install aptitude', stdout=False, sudo=True)

            self.ensure_up_to_date()
            self.ensure_package_installed('curl')



    def ensure_gpg_key(self, url = None, file = None):
        '''
        Ensures that the specified gpg key is imported into aptitude.
        <em>Parameters</em>
        url - Url of the gpg key file.
        file - Local filesystem file containing gpg file
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    role.ensure_gpg_key('http://some.url.com/to/key.gpg')
                    role.ensure_gpg_key(CURRENT_DIR + '/data/foo.gpg')
                    role.ensure_gpg_key(StringIO(SOME_CONSTANT))
        </pre>
        '''

        def do_url():
            command = "curl %s | apt-key add -" % url
            self.execute(command, stdout=False, sudo=True)

        def do_file():
            temp_dir = self.create_temp_dir()
            key_name = temp_dir + "/key.gpg"
            self.put_file(file, key_name, sudo = True)
            self.execute("apt-key add {}".format(key_name), sudo=True)

        if not url and not file or (url and file):
            raise ConfigurationError("Must specify url either file parameter of ensure_gpg_key (not both(")

        if url:
            do_url()

        if file:
            do_file()

    def has_source(self, source_string):
        '''
        Returns True if the specified repository is in aptitude's list of repositories.
        <em>Parameters</em>
        source_string - repository string
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    if role.has_source('deb http://www.las.ic.unicamp.br/pub/ubuntu/ natty main restricted'):
                        # do something
        </pre>
        '''

        result = self.execute('grep -ilR \'^%s\' /etc/apt/sources.list /etc/apt/sources.list.d | wc -l' % source_string, stdout=False, sudo=True)
        return int(result) != 0

    def ensure_aptitude_source(self, source_string):
        '''
        Ensures that the specified repository is in aptitude's list of repositories.
        <em>Parameters</em>
        source_string - repository string
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    role.ensure_aptitude_source('deb http://www.las.ic.unicamp.br/pub/ubuntu/ natty main restricted')
        </pre>
        '''
        if self.has_source(source_string):
            return False

        self.log("Aptitude source %s not found! Adding it..." % source_string)
        command = 'echo "%s" >> /etc/apt/sources.list' % source_string
        self.execute(command, stdout=False, sudo=True)
        return True

    def ensure_package_removed(self, package_name, purge = False):

        operation = "purge" if purge else "remove"

        if isinstance(package_name, (list, set, tuple)):
            if any(map(self.is_package_installed, package_name)):
                self.log("Removing packages {}".format(package_name))
                self.execute("aptitude -y {} {}".format(operation, " ".join(package_name)), sudo=True)
        else:
            if self.is_package_installed(package_name):
                self.log("Removing package {}".format(package_name))
                self.execute("aptitude -y {} {}".format(operation, package_name), sudo=True)



    def override_sources_list(self, sources_list_file):
        close = False
        if isinstance(sources_list_file, basestring):
            close = True
            sources_list_file = open(sources_list_file)
        tempfile = self.create_temp_file()
        self.log("Overriding aptitude sources")
        self.put_file(sources_list_file, to_file=tempfile, stdout=True)
        self.execute('cat "{}" > /etc/apt/sources.list'.format(tempfile), stdout=False, sudo=True)
        if close:
            sources_list_file.close()
        self.force_update()


    @property
    def update_date_file(self):
        '''
        Returns the path for the file that contains the last update date to aptitudes's list of packages.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    file_path = role.update_date_file
        </pre>
        '''
        return join(self.remote_temp_dir(), 'last_aptitude_update')

    def store_update_date(self):
        '''
        Updates the date in the <em>update_date_file</em>.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    role.store_update_date()
        </pre>
        '''
        self.execute('echo "%s" > %s' % (datetime.now().strftime(self.time_format), self.update_date_file), stdout=False, sudo=True)

    def get_last_update_date(self):
        '''
        Returns the date in the <em>update_date_file</em>.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    last_update = role.get_last_update_date()
        </pre>
        '''
        if not self.remote_exists(self.update_date_file):
            return None

        date = datetime.strptime(self.read_remote_file(self.update_date_file), self.time_format)
        return date

    def ensure_up_to_date(self):
        '''
        Makes sure aptitude's repository is updated if it hasn't been updated in the last 30 minutes.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    role.ensure_up_to_date()
        </pre>
        '''
        last_updated = self.get_last_update_date()
        if not self.key in self.context and (not last_updated or (datetime.now() - last_updated > timedelta(minutes=30))):
            self.force_update()

    def force_update(self):
        '''
        Forces an update to aptitude's repository.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    role.force_update()
        </pre>
        '''
        self.log('Updating aptitude sources...')
        self.execute('%s update' % self.aptitude, stdout=False, sudo=True)
        self.store_update_date()
        self.log('Aptitude sources up-to-date')
        self.context[self.key] = True

    def is_package_installed(self, package_name):
        '''
        Returns True if the given package is installed via aptitude, False otherwise.
        <em>Parameters</em>
        package_name - Name of the package to verify
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    if role.is_package_installed('nginx'):
                        # do something
        </pre>
        '''

        with settings(warn_only=True):
            return package_name in self.execute("dpkg -l | egrep 'ii[ ]*%s\\b'" % package_name, stdout=False, sudo=True)

    def ensure_package_installed(self, package_name, stdout=False, sudo=True):
        '''
        Ensures that the given package is installed via aptitude.
        <em>Parameters</em>
        package_name - Name of the package to install
        stdout - Indicates whether install progress should be shown to stdout. Defaults to False.
        sudo - Indicates whether the package should be installed with the super user. Defaults to True.
        <em>Exceptions</em>
        Raises provy.more.debian.PackageNotFound if the package is not found in the repositories.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    role.ensure_package_installed('nginx')
        </pre>
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
        <em>Parameters</em>
        package - Name of the package to check
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AptitudeRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    role.package_exists('nginx') # True
        </pre>
        '''
        try:
            return bool(self.execute('%s show %s' % (self.aptitude, package), stdout=False))
        except SystemExit:
            return False

def UninstallPackages(package_list, purge = False):
    """
    Example usage::
        servers = {
            'new': {
                'address': '192.168.57.20',
                'user': USERNAME,
                'roles': [
                    UninstallPackages(("exim4", "exim4-base", "exim4-config", "exim4-deamon-light", "bsd-mailx"))
                ]
                }
            }
        }
    """
    class PackageRole(Role):
        def provision(self):
            with self.using(AptitudeRole) as role:
                role.ensure_package_removed(package_list, purge=purge)
    return PackageRole

def InstallPackages(package_list):
    """
    Example usage:
    servers = {
            'new': {
                'address': '192.168.57.20',
                'user': USERNAME,
                'roles': [
                    InstallPackages(("exim4", "exim4-base", "exim4-config", "exim4-deamon-light", "bsd-mailx"))
                ]
                }
            }
        }

    """
    class PackageRole(Role):
        def provision(self):
            with self.using(AptitudeRole) as role:
                for pack in package_list:
                    role.ensure_package_installed(pack)
    return PackageRole

class PackageNotFound(Exception):
    '''Should be raised when a package doesn't exist.'''
