#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision packages installed via the Yum package manager for CentOS distributions.
'''

from os.path import join
from datetime import datetime, timedelta

from fabric.api import settings

from provy.core import Role


class YumRole(Role):
    '''
    This role provides package management operations with Yum within CentOS distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.centos import YumRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(YumRole) as role:
                role.ensure_package_installed('nginx')
    </pre>
    '''

    time_format = "%d-%m-%y %H:%M:%S"
    key = 'yum-up-to-date'

    def provision(self):
        '''
        Installs Yum dependencies. This method should be called upon if overriden in base classes, or Yum won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import YumRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(YumRole) # does not need to be called if using with block.
        </pre>
        '''
        self.ensure_up_to_date()
        self.ensure_package_installed('curl')

    def ensure_gpg_key(self, url):
        '''
        Ensures that the specified gpg key is imported into rpm.
        <em>Parameters</em>
        url - Url of the gpg key file.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import YumRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(YumRole) as role:
                    role.ensure_gpg_key('http://some.url.com/to/key.gpg')
        </pre>
        '''
        command = "curl %s | rpm --import -" % url
        self.execute(command, stdout=False, sudo=True)

    def has_source(self, source_string):
        '''
        Ensures that the specified repository is in yum's list of repositories.
        <em>Parameters</em>
        source_string - repository string
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import YumRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(YumRole) as role:
                    if role.has_source('some-path-to-a-repo'):
                        # do something
        </pre>
        '''
        return source_string in self.execute('cat /etc/yum.repos.d/CentOS-Base.repo', stdout=False, sudo=True)

    def ensure_yum_source(self, source_string):
        '''
        Ensures that the specified repository is in yum's list of repositories.
        <em>Parameters</em>
        source_string - repository string
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import YumRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(YumRole) as role:
                    role.ensure_yum_source('some-path-to-a-repo')
        </pre>
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
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import YumRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(YumRole) as role:
                    file_path = role.update_date_file
        </pre>
        '''
        return join(self.remote_temp_dir(), 'last_yum_update')

    def store_update_date(self):
        '''
        Updates the date in the <em>update_date_file</em>.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import YumRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(YumRole) as role:
                    role.store_update_date()
        </pre>
        '''

        self.execute('echo "%s" > %s' % (datetime.now().strftime(self.time_format), self.update_date_file), stdout=False)

    def get_last_update_date(self):
        '''
        Returns the date in the <em>update_date_file</em>.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import YumRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(YumRole) as role:
                    last_update = role.get_last_update_date()
        </pre>
        '''
        if not self.remote_exists(self.update_date_file):
            return None

        date = datetime.strptime(self.read_remote_file(self.update_date_file), self.time_format)
        return date

    def ensure_up_to_date(self):
        '''
        Makes sure Yum's repository is updated if it hasn't been updated in the last 30 minutes.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import YumRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(YumRole) as role:
                    role.ensure_up_to_date()
        </pre>
        '''

        last_updated = self.get_last_update_date()
        if not self.key in self.context and (not last_updated or (datetime.now() - last_updated > timedelta(minutes=30))):
            self.force_update()

    def force_update(self):
        '''
        Forces an update to Yum's repository.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import YumRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(YumRole) as role:
                    role.force_update()
        </pre>
        '''
        self.log('Updating yum sources...')
        self.execute('yum clean all', stdout=False, sudo=True)
        self.store_update_date()
        self.log('Yum sources up-to-date')
        self.context[self.key] = True

    def is_package_installed(self, package_name):
        '''
        Returns True if the given package is installed via Yum, False otherwise.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import YumRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(YumRole) as role:
                    if role.is_package_installed('nginx'):
                        # do something
        </pre>
        '''
        package = self.execute(
                'rpm -qa %s' % package_name, stdout=False, sudo=True,
            )
        return bool(package)

    def ensure_package_installed(self, package_name):
        '''
        Ensures that the given package is installed via Yum.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import YumRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(YumRole) as role:
                    role.ensure_package_installed('nginx')
        </pre>
        '''
        if not self.is_package_installed(package_name):
            self.log('%s is not installed (via yum)! Installing...' % package_name)
            self.execute('yum install -y %s' % package_name, stdout=False, sudo=True)
            self.log('%s is installed (via yum).' % package_name)
            return True
        return False
