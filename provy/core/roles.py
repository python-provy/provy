#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Module responsible for the base Role and its operations.
'''

import codecs
from contextlib import contextmanager
import os
from os.path import exists, split, dirname, isabs
from datetime import datetime
from tempfile import gettempdir, NamedTemporaryFile

import fabric.api
from jinja2 import Environment, PackageLoader, FileSystemLoader


class UsingRole(object):
    '''ContextManager that allows using Roles in other Roles.'''
    def __init__(self, role, prov, context):
        self.role = role
        self.prov = prov
        self.context = context

    def __enter__(self):
        if self.role in self.context['used_roles']:
            self.role_instance = self.context['used_roles'][self.role]
        else:
            self.role_instance = self.role(self.prov, self.context)
            self.context['used_roles'][self.role] = self.role_instance
        self.role_instance.provision()
        self.context['roles_in_context'][self.role] = self.role_instance
        return self.role_instance

    def __exit__(self, exc_type, exc_value, traceback):
        role = self.role(self.prov, self.context)
        if self.role in self.context['roles_in_context']:
            del self.context['roles_in_context'][self.role]
        role.schedule_cleanup()


class Role(object):
    '''
    Base Role class. This is the class that is inherited by all provy's roles.
    This class provides many utility methods for interacting with the remote server.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role

    class MySampleRole(Role):
        def provision(self):
            self.register_template_loader('my.full.namespace')
            self.execute('ls /home/myuser', sudo=False, stdout=False)
    </pre>
    '''
    def __init__(self, prov, context):
        if 'used_roles' not in context:
            context['used_roles'] = {}
        if 'roles_in_context' not in context:
            context['roles_in_context'] = {}
        self.prov = prov
        self.context = context

    def register_template_loader(self, package_name):
        '''
        Register the <<package_name>> module as a valid source for templates in jinja2.
        Jinja2 will look inside a folder called 'templates' in the specified module.
        It is paramount that this module can be imported by python. The path must be well-known or be a sub-path of the provyfile.py directory.
        <em>Parameters</em>
        package_name - Full name of the module that jinja2 will try to import.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.register_template_loader('my.full.namespace')
        </pre>
        '''
        if package_name not in self.context['registered_loaders']:
            self.context['loader'].loaders.append(PackageLoader(package_name))
            self.context['registered_loaders'].append(package_name)

    def log(self, msg):
        '''
        Logs a message to the console with the hour prepended.
        <em>Parameters</em>
        msg - Message to log.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.log('Hello World')
        </pre>
        '''
        print '[%s] %s' % (datetime.now().strftime('%H:%M:%S'), msg)

    def schedule_cleanup(self):
        '''
        Makes sure that this role will be cleaned up properly after the server has been provisioned. Call this method in your provision method if you need your role's cleanup method to be called.
        <strong>Warning</strong>: If you are using the proper ways of calling roles (provision_role, using) in your role, you do not need to call this method.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.schedule_cleanup()
        </pre>
        '''
        has_role = False
        for role in self.context['cleanup']:
            if role.__class__ == self.__class__:
                has_role = True

        if not has_role:
            self.context['cleanup'].append(self)

    def provision_role(self, role):
        '''
        Provisions a role inside your role. This method is the way to call other roles if you don't need to call any methods other than provision.
        provision_role keeps the context and lifecycle for the current server when calling the role and makes sure it is disposed correctly.
        <em>Parameters</em>
        role - The role to be provisioned. Needs to be a provy.core.Role subclass.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(SomeOtherRole)
        </pre>
        '''
        instance = role(self.prov, self.context)
        instance.provision()
        instance.schedule_cleanup()

    def provision(self):
        '''
        Base provision method. This is meant to be overriden and does not do anything.
        The provision method of each Role is what provy calls on to provision servers.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                pass
        </pre>
        '''
        pass

    def cleanup(self):
        '''
        Base cleanup method. This is meant to be overriden and does not do anything.
        The cleanup method is the method that provy calls after all Roles have been provisioned and is meant to allow Roles to perform any cleaning of resources or finish any pending operations.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def cleanup(self):
                pass
        </pre>
        '''
        pass

    @contextmanager
    def __showing_command_output(self, show=True):
        if show:
            yield
        else:
            with fabric.api.settings(
                fabric.api.hide('warnings', 'running', 'stdout', 'stderr')
            ):
                yield

    def execute(self, command, stdout=True, sudo=False, user=None):
        '''
        This method is the bread and butter of provy and is a base for most other methods that interact with remote servers.
        It allows you to perform any shell action in the remote server. It is an abstraction over fabric run and sudo methods.
        <em>Parameters</em>
        command - The command to be executed.
        stdout - If you specify this argument as False, the standard output of the command execution will not be displayed in the console. Defaults to True.
        sudo - Specifies whether this command needs to be run as the super-user. Doesn't need to be provided if the "user" parameter (below) is provided. Defaults to False.
        user - If specified, will be the user with which the command will be executed. Defaults to None.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.execute('ls /', stdout=False, sudo=True)
                self.execute('ls /', stdout=False, user='vip')
        </pre>
        '''
        with self.__showing_command_output(stdout):
            return self.__execute_command(command, sudo=sudo, user=user)

    def __execute_command(self, command, sudo=False, user=None):
        if sudo or (user is not None):
            return fabric.api.sudo(command, user=user)
        return fabric.api.run(command)

    def execute_local(self, command, stdout=True, sudo=False, user=None):
        '''
        Allows you to perform any shell action in the local machine. It is an abstraction over the fabric.api.local method.
        <em>Parameters</em>
        command - The command to be executed.
        stdout - If you specify this argument as False, the standard output of the command execution will not be displayed in the console. Defaults to True.
        sudo - Specifies whether this command needs to be run as the super-user. Doesn't need to be provided if the "user" parameter (below) is provided. Defaults to False.
        user - If specified, will be the user with which the command will be executed. Defaults to None.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.execute_local('ls /', stdout=False, sudo=True)
                self.execute_local('ls /', stdout=False, user='vip')
        </pre>
        '''
        with self.__showing_command_output(stdout):
            return self.__execute_local_command(command, sudo=sudo, user=user)

    def __execute_local_command(self, command, sudo=False, user=None):
        if user is not None:
            command = 'sudo -u %s %s' % (user, command)
        elif sudo:
            command = 'sudo %s' % command
        return fabric.api.local(command, capture=True)

    def execute_python(self, command, stdout=True, sudo=False):
        '''
        Just an abstraction over execute. This method executes the python code that is passed with python -c.
        <em>Parameters</em>
        command - The Python command to be executed.
        stdout - If you specify this argument as False, the standard output of the command execution will not be displayed in the console. Defaults to True.
        sudo - Specifies whether this command needs to be run as the super-user. Doesn't need to be provided if the "user" parameter (below) is provided. Defaults to False.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.python_execute('import os; print os.curdir',
                                    stdout=False, sudo=True)
        </pre>
        '''
        return self.execute('''python -c "%s"''' % command, stdout=stdout, sudo=sudo)

    def get_logged_user(self):
        '''
        Returns the currently logged user in the remote server.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.context['my-user'] = self.get_logged_user()
        </pre>
        '''
        return self.execute('whoami', stdout=False)

    def local_exists(self, file_path):
        '''
        Returns True if the file exists locally.
        <em>Parameters</em>
        file_path - The path to check.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                if self.local_exists('/tmp/my-file'):
                    # do something
        </pre>
        '''
        return exists(file_path)

    def remote_exists(self, file_path):
        '''
        Returns True if the file exists in the remote server.
        <em>Parameters</em>
        file_path - The path to check.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                if self.remote_exists('/tmp/my-file'):
                    # do something
        </pre>
        '''
        return self.execute('test -f %s; echo $?' % file_path, stdout=False, sudo=True) == '0'

    def remote_exists_dir(self, file_path):
        '''
        Returns True if the directory exists in the remote server.
        <em>Parameters</em>
        file_path - The path to check.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                if self.remote_exists_dir('/tmp'):
                    # do something
        </pre>
        '''
        return self.execute('test -d %s; echo $?' % file_path, stdout=False, sudo=True) == '0'

    def local_temp_dir(self):
        '''
        Returns the path of a temporary directory in the local machine.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.context['source_dir'] = self.local_temp_dir()
        </pre>
        '''
        return gettempdir()

    def remote_temp_dir(self):
        '''
        Returns the path of a temporary directory in the remote server.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.context['target_dir'] = self.remote_temp_dir()
        </pre>
        '''
        return self.execute_python('from tempfile import gettempdir; print gettempdir()', stdout=False)

    def ensure_dir(self, directory, owner=None, sudo=False):
        '''
        Make sure the specified directory exists in the remote server.
        <em>Parameters</em>
        directory - Directory to be created if it does not exist.
        owner - If specified, the directory will be created under this user, otherwise the currently logged user is the owner.
        sudo - If specified, the directory is created under the super-user. This is particularly useful in conjunction with the owner parameter, to create folders for the owner where only the super-user can write.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.ensure_dir('/etc/my-path', owner='myuser', sudo=True)
        </pre>
        '''
        if owner:
            sudo = True

        if not self.remote_exists_dir(directory):
            self.execute('mkdir -p %s' % directory, stdout=False, sudo=sudo)

        if owner:
            self.change_path_owner(directory, owner)

    def change_dir_owner(self, directory, owner):
        '''
        Deprecated. Please use change_path_owner instead.
        <em>Parameters</em>
        directory - Directory to change owner.
        owner - User that should own this directory.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.change_dir_owner(directory='/etc/my-path', owner='someuser')
        </pre>
        '''
        self.log('"change_dir_owner" is deprecated, please use "change_path_owner" instead.')
        self.change_path_owner(directory, owner)

    def change_file_owner(self, path, owner):
        '''
        Deprecated. Please use change_path_owner instead.
        <em>Parameters</em>
        path - Path of the file.
        owner - User that should own this file.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.change_file_owner(path='/etc/init.d/someapp',
                                       owner='someuser')
        </pre>
        '''
        self.log('"change_file_owner" is deprecated, please use "change_path_owner" instead.')
        self.change_path_owner(path, owner)

    def change_path_owner(self, path, owner):
        '''
        Changes the owner of a given path. Please be advised that this method is recursive, so if the path is a directory, all contents of it will belong to the specified owner.
        <em>Parameters</em>
        path - Path to have its owner changed.
        owner - User that should own this path.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.change_path_owner(path='/etc/my-path', owner='someuser')
        </pre>
        '''
        self.execute('chown -R %s %s' % (owner, path), stdout=False, sudo=True)

    def get_object_mode(self, path):
        '''
        Returns the mode of a given object. Raises IOError if the path doesn't exist.
        <em>Parameters</em>
        path - Path of the given object.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                if self.get_object_mode('/home/user/logs') == 644:
                    # do something
        </pre>
        '''
        if not self.remote_exists(path) and not self.remote_exists_dir(path):
            raise IOError('The file at path %s does not exist' % path)
        return int(self.execute('stat -c %%a %s' % path, stdout=False, sudo=True))

    def change_path_mode(self, path, mode, recursive=False):
        '''
        Changes the mode of a given path.
        <em>Parameters</em>
        path - Path to have its mode changed.
        mode - Mode to change to.
        recursive - Indicates if the mode of the objects in the path should be changed recursively. Defaults to False.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.change_path_mode(directory='/home/user/logs',
                                     mode=644,
                                     recursive=True)
        </pre>
        '''
        options = ""
        if recursive:
            options += "-R "

        previous_mode = self.get_object_mode(path)
        if previous_mode != mode or recursive:
            self.execute('chmod %s%s %s' % (options, mode, path), stdout=False, sudo=True)
            self.log("Path %s had mode %s. Changed it %sto %s." % (path, previous_mode, recursive and "recursively " or "", mode))

    def change_dir_mode(self, path, mode, recursive=False):
        '''
        Deprecated. Please use change_path_mode instead.
        <em>Parameters</em>
        path - Path of the directory.
        mode - Mode of the directory.
        recursive - Indicates if the mode of the objects in the path should be changed recursively.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.change_dir_mode(directory='/home/user/logs',
                                     mode=644,
                                     recursive=True)
        </pre>
        '''
        self.change_path_mode(path, mode, recursive=recursive)

    def change_file_mode(self, path, mode):
        '''
        Deprecated. Please use change_path_mode instead.
        <em>Parameters</em>
        path - Path of the file.
        mode - Mode of the file.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.change_file_mode(path='/etc/init.d/someapp',
                                      mode=777)
        </pre>
        '''
        self.change_path_mode(path, mode)

    def md5_local(self, path):
        '''
        Calculates an md5 hash for a given file in the local system. Returns None if file does not exist.
        <em>Parameters</em>
        path - Path of the local file.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                hash = self.md5_local('/tmp/my-file')
        </pre>
        '''
        if not self.local_exists(path):
            return None

        result = self.execute_local(self.__md5_hash_command(path), stdout=False, sudo=True)
        return result.strip()

    def md5_remote(self, path):
        '''
        Calculates an md5 hash for a given file in the remote server. Returns None if file does not exist.
        <em>Parameters</em>
        path - Path of the remote file.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                hash = self.md5_remote('/tmp/my-file')
        </pre>
        '''
        if not self.remote_exists(path):
            return None

        result = self.execute(self.__md5_hash_command(path), stdout=False, sudo=True)
        return result.strip()

    def __md5_hash_command(self, path):
        return 'md5sum %s | cut -d " " -f 1' % path

    def remove_dir(self, path, sudo=False, recursive=False):
        '''
        Removes a directory in the remote server. Returns True in the event of the directory actually been removed. False otherwise.
        <em>Parameters</em>
        path - Path of the remote directory.
        sudo - Indicates whether the directory should be removed by the super-user. Defaults to False.
        recursive - Indicates whether the directory should be removed recursively or not. Defaults to False.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.remove_dir('/tmp/my-dir', sudo=True, recursive=True)
        </pre>
        '''
        if self.remote_exists_dir(path):
            if recursive:
                command = 'rm -rf %s'
            else:
                command = 'rmdir %s'
            self.execute(command % path, stdout=False, sudo=sudo)
            self.log('%s removed!' % path)
            return True
        return False

    def remove_file(self, path, sudo=False):
        '''
        Removes a file in the remote server. Returns True in the event of the file actually been removed. False otherwise.
        <em>Parameters</em>
        path - Path of the remote file.
        sudo - Indicates whether the file should be removed by the super-user. Defaults to False.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.remove_file('/tmp/my-file', sudo=True)
        </pre>
        '''

        if self.remote_exists(path):
            self.execute('rm -f %s' % path, stdout=False, sudo=sudo)
            self.log('%s removed!' % path)
            return True
        return False

    def replace_file(self, from_file, to_file):
        '''
        Deprecated. Please use put_file instead.
        <em>Parameters</em>
        from_file - Path in the local system.
        to_file - Path in the remote system.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.replace_file('/tmp/my-file', '/tmp/my-file')
        </pre>
        '''
        self.put_file(from_file, to_file)

    def remote_symlink(self, from_file, to_file, sudo=False):
        '''
        Creates a symlink in the remote server.
        <em>Parameters</em>
        from_file - Symlink source.
        to_file - Symlink target.
        sudo - Indicates whether the symlink should be created by the super-user.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.remote_symlink('/home/user/my-app',
                                    '/etc/init.d/my-app',
                                    sudo=True)
        </pre>
        '''
        if not self.remote_exists(from_file):
            raise RuntimeError("The file to create a symlink from (%s) was not found!" % from_file)

        command = 'ln -sf %s %s' % (from_file, to_file)
        if self.remote_exists(to_file):
            result = self.execute('ls -la %s' % to_file, stdout=False, sudo=sudo)
            if '->' in result:
                path = result.split('->')[-1].strip()
                if path != from_file:
                    self.log('Symlink has different path(%s). Syncing...' % path)
                    self.execute(command, stdout=False, sudo=sudo)
        else:
            self.log('Symlink not found at %s! Creating...' % from_file)
            self.execute(command, stdout=False, sudo=sudo)

    def __extend_context(self, options):
        extended = {}
        for key, value in self.context.iteritems():
            extended[key] = value
        for key, value in options.iteritems():
            extended[key] = value
        return extended

    def put_file(self, from_file, to_file, sudo=False):
        '''
        Puts a file to the remote server.
        <em>Parameters</em>
        from_file - Source file in the local system.
        to_file - Target path in the remote server.
        sudo - Indicates whether the file should be created by the super-user.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.put('/home/user/my-app',
                         '/etc/init.d/my-app',
                         sudo=True)
        </pre>
        '''
        fabric.api.put(from_file, to_file, use_sudo=sudo)

    def update_file(self, from_file, to_file, owner=None, options={}, sudo=None):
        '''
        One of the most used methods in provy. This method renders a template, then if the contents differ from the remote server (or the file does not exist at the remote server), it sends the results there.
        Again, combining the parameters sudo and owner you can have files that belong to an user that is not a super-user in places that only a super-user can reach.
        Returns True if the file was updated, False otherwise.
        <em>Parameters</em>
        from_file - Template file in the local system.
        to_file - Target path in the remote server.
        owner - Owner for the file in the remote server.
        options - Dictionary of options that can be used in the template.
        sudo - Indicates whether the file should be created by the super-user.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.update_file('/home/user/my-app',
                                 '/etc/init.d/my-app',
                                 owner='my-user',
                                 {
                                    'option_a': 1,
                                    'option_b': 2
                                 },
                                 sudo=True)
        </pre>
        '''
        update_data = None
        try:
            update_data = self._build_update_data(from_file, options, to_file)
            return self._update_file_with_data(to_file, update_data, from_file, sudo, owner)
        finally:
            if update_data and update_data.local_temp_path and exists(update_data.local_temp_path):
                os.remove(update_data.local_temp_path)

    def _update_file_with_data(self, to_file, update_data, from_file, sudo, owner):
        should_create = not self.remote_exists(to_file)
        contents_differ = self._contents_differ(update_data.to_md5, update_data.from_md5)

        if not should_create or contents_differ:
            self.log('Hashes differ %s => %s! Copying %s to server %s!' % (update_data.from_md5, update_data.to_md5, from_file, self.context['host']))

        if should_create or contents_differ:
            self._force_update_file(to_file, sudo, update_data.local_temp_path, owner)
            return True
        return False

    def _build_update_data(self, from_file, options, to_file):
        template = self.render(from_file, options)
        local_temp_path = self.write_to_temp_file(template)
        from_md5 = self.md5_local(local_temp_path)
        to_md5 = self.md5_remote(to_file)

        update_data = UpdateData(local_temp_path, from_md5, to_md5)
        return update_data

    def _contents_differ(self, to_md5, from_md5):
        return self._clean_md5(from_md5) != self._clean_md5(to_md5)

    def _clean_md5(self, md5):
        if md5 is None:
            return None
        return md5.strip()

    def _force_update_file(self, to_file, sudo, local_temp_path, owner):
        if sudo is None and owner is not None:
            sudo = True
        elif sudo is None and owner is None:
            sudo = False

        self.put_file(local_temp_path, to_file, sudo)

        if owner:
            self.change_file_owner(to_file, owner)

    def write_to_temp_file(self, text):
        '''
        Writes some text to a temporary file and returns the file path.
        <em>Parameters</em>
        text - Text to be written to the temp file.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                path = self.write_to_temp_file('some random text')
                self.put_file(path, '/tmp/some-file')
        </pre>
        '''
        local_temp_path = ''
        with NamedTemporaryFile(delete=False) as f:
            content = codecs.encode(text, 'utf-8')
            f.write(content)
            local_temp_path = f.name

        return local_temp_path

    def read_remote_file(self, path, sudo=True):
        '''
        Returns the contents of a remote file.
        <em>Parameters</em>
        path - File path on the remote server.
        sudo - Indicates whether the file should be read by a super-user. Defaults to True.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                last_update = self.read_remote_file('/tmp/last-update')
        </pre>
        '''
        result = self.execute_python("import codecs; print codecs.open('%s', 'r', 'utf-8').read()" % path, stdout=False, sudo=sudo)
        return result

    def render(self, template_file, options={}):
        '''
        Renders a template with the given options and returns the rendered text.
        The template_file parameter should be just the name of the file and not the file path. jinja2 will look for templates at the files directory in the provyfile path, as well as in the templates directory of any registered module (check the <em>register_template_loader</em> method).
        The options parameter will extend the server context, so all context variables (including per-server options) are available to the renderer.
        <em>Parameters</em>
        template_file - Template file path in the local system.
        options - Options to be passed to the template, as a dictionary. Defaults to empty dict.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                contents = self.render('my-template', { 'user': 'heynemann' })
        '''

        if isabs(template_file):
            env = Environment(loader=FileSystemLoader(dirname(template_file)))
            template_path = split(template_file)[-1]
        else:
            env = Environment(loader=self.context['loader'])
            template_path = template_file
        template = env.get_template(template_path)

        return template.render(**self.__extend_context(options))

    def is_process_running(self, process, sudo=False):
        '''
        Returns True if the given process is running (listed in the process listing), False otherwise.
        <em>Parameters</em>
        process - Regular expression string that specifies the process name.
        sudo - Indicates if the process listing should be done by the super-user. Defaults to False.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                if self.is_process_running('nginx', sudo=True):
                    self.execute('pkill nginx', stdout=False, sudo=True)
        '''
        return_code = self.execute('ps aux | egrep %s | egrep -v egrep > /dev/null;echo $?' % process, stdout=False, sudo=sudo)
        return int(return_code) == 0

    def has_line(self, line, file_path):
        '''
        Returns True if the given line of text is present in the given file. Returns False otherwise (even if the file does not exist).
        <em>Parameters</em>
        line - Line of text to verify in the given file.
        file_path - Complete path of the remote file.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                if self.has_line('127.0.0.1 localhost', '/etc/hosts'):
                    pass
        '''
        if not self.remote_exists(file_path):
            return False

        contents = self.read_remote_file(file_path).split('\n')

        for current_line in contents:
            if line.replace(' ', '') == current_line.replace(' ', ''):
                return True
        return False

    def ensure_line(self, line, file_path, owner=None, sudo=False):
        '''
        Ensures that the given line exists in the given file_path. Adds it if it doesn't exist, and creates the file if it doesn't exist.
        <em>Parameters</em>
        line - Line of text to verify in the given file.
        file_path - Complete path of the remote file.
        owner - The user that owns the file. Defaults to None (the context user is used in this case).
        sudo - Execute as sudo? Defaults to False.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.ensure_line('127.0.0.1     localhost', '/etc/hosts')
        '''
        if not self.has_line(line, file_path):
            self.execute('echo "%s" >> %s' % (line, file_path), stdout=False, sudo=sudo, user=owner)
            self.log('Line "%s" not found in %s. Adding it.' % (line, file_path))

    def using(self, role):
        '''
        This method should be used when you want to use a different Role inside your own Role methods.
        It returns a ContextManager object, so this is meant to go inside a <em>with</em> block.
        <em>Parameters</em>
        role - Role to be used.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                with self.using(AptitudeRole) as role:
                    role.ensure_package_installed('nginx')
        '''
        return UsingRole(role, self.prov, self.context)

    def get_distro_info(self):
        '''
        Returns a DistroInfo with valuable information regarding the distribution of the server.
        In the backgrounds, what it does is to run
        $ lsb_release -a
        in the server, so you might want to check which results are usual for your distribution.
        <em>Sample Usage</em>
        <pre class="sh_python">
        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                distro_info = self.role.get_distro_info()

                # Supposing the server is a Debian Squeeze, the following statements will probably be true:
                distro_info.distributor_id == 'Debian'
                distro_info.description == 'Debian GNU/Linux 6.0.5 (squeeze)'
                distro_info.release == '6.0.5'
                distro_info.codename == 'squeeze'

                # Supposing the server is a Ubuntu Precise Pangolin, the following statements will probably be true:
                distro_info.distributor_id == 'Ubuntu'
                distro_info.description == 'Ubuntu 12.04.1 LTS'
                distro_info.release == '12.04'
                distro_info.codename == 'precise'

                # Supposing the server is a CentOS, the following statements may be true:
                distro_info.lsb_version == ':core-4.0-ia32:core-4.0-noarch:graphics-4.0-ia32:graphics-4.0-noarch:printing-4.0-ia32:printing-4.0-noarch'
                distro_info.distributor_id == 'CentOS'
                distro_info.description == 'CentOS release 5.8 (Final)'
                distro_info.release == '5.8'
                distro_info.codename == 'Final'
        '''
        raw_distro_info = self.execute('lsb_release -a')
        distro_info_lines = raw_distro_info.split('\n')
        distro_info = DistroInfo()

        for line in distro_info_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info_property = key.lower().replace(' ', '_')
                setattr(distro_info, info_property, value.strip())

        return distro_info


class DistroInfo(object):
    '''
    Value object used to contain distribution information.
    Refer to Role.get_distro_info() usage.
    '''
    lsb_version = None
    distributor_id = None
    description = None
    release = None
    codename = None


class UpdateData(object):
    '''
    Value object used in the update_file method.
    '''
    def __init__(self, local_temp_path, from_md5, to_md5):
        self.local_temp_path = local_temp_path
        self.from_md5 = from_md5
        self.to_md5 = to_md5
