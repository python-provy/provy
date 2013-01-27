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
import uuid
import StringIO


class UsingRole(object):
    '''
    This is the contextmanager that allows using :class:`Roles <Role>`
    in other :class:`Roles <Role>`, in a nested manner.

    Don't use this directly; Instead, use the base
    :class:`Role`'s :meth:`using <Role.using>` method.
    '''
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

    This class provides many utility methods for interacting with the remote
    server.

    Example:
    ::

        from provy.core import Role

        class MySampleRole(Role):
            def provision(self):
                self.register_template_loader('my.full.namespace')
                self.execute('ls /home/myuser', sudo=False, stdout=False)
    '''
    def __init__(self, prov, context):
        if 'used_roles' not in context:
            context['used_roles'] = {}
        if 'roles_in_context' not in context:
            context['roles_in_context'] = {}
        self._paths_to_remove = set()  # TODO: Anyone merging this: it holds
        # list of paths that will be removed on self.cleanup()
        # I feel this should be somewhere in context, but then it would be
        # shared by all roles (which is bad).
        self.prov = prov
        self.context = context

    def register_template_loader(self, package_name):
        '''
        Register the ``package_name`` module as a valid source for templates in
        `Jinja2 <http://jinja.pocoo.org/>`_.

        `Jinja2 <http://jinja.pocoo.org/>`_ will look inside a folder called
        *templates* in the specified module.

        It is paramount that this module can be imported by python. The path
        must be well-known or be a sub-path of the provyfile.py directory.

        :param package_name: Full name of the module that
            Jinja2 <http://jinja.pocoo.org/>`_ will try to import.
        :type package_name: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.register_template_loader('my.full.namespace')
        '''
        if package_name not in self.context['registered_loaders']:
            self.context['loader'].loaders.append(PackageLoader(package_name))
            self.context['registered_loaders'].append(package_name)

    def log(self, msg):
        '''
        Logs a message to the console with the hour prepended.

        :param msg: Message to log.
        :type msg: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.log('Hello World')
        '''
        print '[%s] %s' % (datetime.now().strftime('%H:%M:%S'), msg)

    @property
    def roles_in_context(self):
        return self.context.get("roles_in_context", tuple([]))

    def schedule_cleanup(self):
        '''
        Makes sure that this role will be cleaned up properly after the server
        has been provisioned. Call this method in your provision method if you
        need your role's cleanup method to be called.

        .. note:: If you are using the proper ways of calling roles
        (:meth:`provision_role`, :meth:`using`) in your role, you do
        not need to call this method.

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.schedule_cleanup()
        '''
        has_role = False
        for role in self.context['cleanup']:
            if role.__class__ == self.__class__:
                has_role = True

        if not has_role:
            self.context['cleanup'].append(self)

    def provision_role(self, role):
        '''
        Provisions a role inside your role. This method is the way to call
        other roles if you don't need to call any methods other than provision.

        ``provision_role`` keeps the context and lifecycle for the current
        server when calling the role and makes sure it is disposed correctly.

        .. note:: There's no need to call this method, if you're using
        the :meth:`using` as a context manager.

        :param role: The role to be provisioned.
        :type role: :class:`Role`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(SomeOtherRole)
        '''
        instance = role(self.prov, self.context)
        instance.provision()
        instance.schedule_cleanup()

    def provision(self):
        '''
        Base provision method. This is meant to be overriden
        and does not do anything.

        The ``provision`` method of each ``Role`` is what provy
        calls on to provision servers.

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    pass
        '''
        pass

    def cleanup(self):
        '''
        Base cleanup method. It cleans temporary files and directories created
        on server using :meth:`create_remote_temp_file`.

        The ``cleanup`` method is the method that provy calls after all
        ``Roles`` have been provisioned and is meant to allow ``Roles``
        to perform any cleaning of resources or finish any pending operations.

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def cleanup(self):
                    pass
        '''
        for path in self._paths_to_remove:
            try:
                self.remove_dir(path, True, True)
            except Exception:
                self.log("Couldn't clean path {}".format(path))

    @contextmanager
    def __showing_command_output(self, show=True):
        if show:
            yield
        else:
            with fabric.api.settings(
                fabric.api.hide('warnings', 'running', 'stdout', 'stderr')
            ):
                yield

    @contextmanager
    def __cd(self, cd=None):
        """
            If cd is not none will use fabric.api.cd else this is a noop.
        """
        if cd is not None:
            with fabric.api.cd(cd):
                yield
        else:
            yield

    def execute(self, command, stdout=True, sudo=False, user=None, cwd=None):
        '''
        This method is the bread and butter of provy and is a base for most
        other methods that interact with remote servers.

        It allows you to perform any shell action in the remote server.
        It is an abstraction over `fabric <https://fabric.readthedocs.org/en/latest/>`_
        `run <https://fabric.readthedocs.org/en/latest/api/core/operations.html#fabric.operations.run>`_
        and `sudo <https://fabric.readthedocs.org/en/latest/api/core/operations.html#fabric.operations.sudo>`_ methods.

        :param command: The command to be executed.
        :type command: :class:`str`
        :param stdout: If you specify this argument as False, the standard
        output of the command execution will not be displayed in the console.
        Defaults to True.
        :type stdout: :class:`bool`
        :param sudo: Specifies whether this command needs to be run as the
        super-user. Doesn't need to be provided if the "user" parameter (below)
        is provided. Defaults to False.
        :type sudo: :class:`bool`
        :param user: If specified, will be the user with which the command
        will be executed. Defaults to None.
        :type user: :class:`str`
        :param cwd: Represents a directory on remote server.If specified we will
         cd into that directory before executing command. Current path will be
         *unchanged* after the call.
        :type cwd: :class:`str`

        :return: The execution result
        :rtype: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.execute('ls /', stdout=False, sudo=True)
                    self.execute('ls /', stdout=False, user='vip')
        '''
        with self.__showing_command_output(stdout):
            with self.__cd(cwd):
                return self.__execute_command(command, sudo=sudo, user=user)

    def __execute_command(self, command, sudo=False, user=None):
        if sudo or (user is not None):
            return fabric.api.sudo(command, user=user)
        return fabric.api.run(command)

    def execute_local(self, command, stdout=True, sudo=False, user=None):
        '''
        Allows you to perform any shell action in the local machine. It is an
        abstraction over the `fabric.api.local <https://fabric.readthedocs.org/en/latest/api/core/operations.html#fabric.operations.local>`_ method.

        :param command: The command to be executed.
        :type command: :class:`str`
        :param stdout: If you specify this argument as False, the standard
        output of the command execution will not be displayed in the console.
        Defaults to :class:`True`.
        :type stdout: :class:`bool`
        :param sudo: Specifies whether this command needs to be run as the
        super-user. Doesn't need to be provided if the "user" parameter (below)
        is provided. Defaults to :class:`False`.
        :type sudo: :class:`bool`
        :param user: If specified, will be the user with which the command will
        be executed. Defaults to :class:`None`.
        :type user: :class:`str`

        :return: The execution result
        :rtype: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.execute_local('ls /', stdout=False, sudo=True)
                    self.execute_local('ls /', stdout=False, user='vip')
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
        Just an abstraction over execute. This method executes the python
        code that is passed with python -c.

        :param command: The command to be executed.
        :type command: :class:`str`
        :param stdout: If you specify this argument as False, the standard
        output of the command execution will not be displayed in the console.
        Defaults to :class:`True`.
        :type stdout: :class:`bool`
        :param sudo: Specifies whether this command needs to be run as the
        super-user. Doesn't need to be provided if the "user" parameter (below)
        is provided. Defaults to :class:`False`.
        :type sudo: :class:`bool`

        :return: The execution result
        :rtype: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.python_execute('import os; print os.curdir',
                                                stdout=False, sudo=True)
        '''
        return self.execute('''python -c "%s"''' % command, stdout=stdout, sudo=sudo)

    def execute_python_script(self, script, stdout=True, sudo=False):
        script_file = self.create_remote_temp_file("script", "py")
        if isinstance(script, basestring):
            script = StringIO.StringIO(script)

        self.put_file(script, script, sudo)
        try:
            self.execute("python -f {}".format(script_file), str, sudo)
        finally:
            self.remove_file(script_file, sudo)

    def remote_list_directory(self, path):
        """
            Lists contents of remote directory and returns them as a python
            list.
        """
        import json  # in case someone uses python 2.6
        result = self.execute_python('''import os, json; print json.dumps(os.listdir('{}'))'''.format(path))
        contents = json.loads(result)
        return contents

    def get_logged_user(self):
        '''
        Returns the currently logged user in the remote server.

        :return: The logged user
        :rtype: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.context['my-user'] = self.get_logged_user()
        '''
        return self.execute('whoami', stdout=False)

    def local_exists(self, file_path):
        '''
        Returns True if the file exists locally.

        :param file_path: The path to check.
        :type file_path: :class:`str`

        :return: Whether the file exists or not
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    if self.local_exists('/tmp/my-file'):
                        pass
        '''
        return exists(file_path)

    def remote_exists(self, file_path):
        '''
        Returns True if the file exists in the remote server.

        :param file_path: The path to check.
        :type file_path: :class:`str`

        :return: Whether the file exists or not
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    if self.remote_exists('/tmp/my-file'):
                        pass
        '''
        return self.execute('test -f %s; echo $?' % file_path, stdout=False,
                            sudo=True) == '0'

    def remote_exists_dir(self, file_path):
        '''
        Returns True if the directory exists in the remote server.

        :param file_path: The path to check.
        :type file_path: :class:`str`

        :return: Whether the directory exists or not
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    if self.remote_exists_dir('/tmp'):
                        pass
        '''
        return self.execute('test -d %s; echo $?' % file_path, stdout=False,
                            sudo=True) == '0'

    def local_temp_dir(self):
        '''
        Returns the path of a temporary directory in the local machine.

        :return: The temp dir path
        :rtype: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.context['source_dir'] = self.local_temp_dir()
        '''
        return gettempdir()

    def remote_temp_dir(self):
        '''
        Returns the path of a temporary directory in the remote server.

        :return: The temp dir path
        :rtype: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.context['target_dir'] = self.remote_temp_dir()
        '''
        return self.execute_python('from tempfile import gettempdir; print gettempdir()', stdout=False)

    def create_remote_temp_file(self, prefix='', suffix='', cleanup=False):
        """
            Creates random unique file name, it is save to put write to this
            file on remote server.
        """
        file_name = "{}/{}{}.{}".format(self.remote_temp_dir(), prefix,
                                        str(uuid.uuid4()), suffix)
        if cleanup:
            self._paths_to_remove.add(file_name)
        return file_name

    def create_remote_temp_dir(self, dirname=None, owner=None, chmod=None, cleanup=True):

        if dirname is None:
            dirname = str(uuid.uuid4())

        dirname = "{}/{}".format(self.remote_temp_dir(), dirname)

        self.ensure_dir(dirname, owner, owner is not None)

        if chmod is not None:
            self.change_dir_mode(dirname, chmod)

        if cleanup:
            self._paths_to_remove.add(dirname)

        return dirname

    def ensure_dir(self, directory, owner=None, sudo=False):
        '''
        Make sure the specified directory exists in the remote server.

        :param directory: Directory to be created if it does not exist.
        :type directory: :class:`str`
        :param owner: If specified, the directory will be created under this user, otherwise the currently logged user is the owner.
        :type owner: :class:`str`
        :param sudo: If specified, the directory is created under the super-user. This is particularly useful in conjunction with the owner parameter, to create folders for the owner where only the super-user can write.
        :type sudo: :class:`bool`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.ensure_dir('/etc/my-path', owner='myuser', sudo=True)
        '''
        if owner:
            sudo = True

        if not self.remote_exists_dir(directory):
            self.execute('mkdir -p %s' % directory, stdout=False, sudo=sudo)

        if owner:
            self.change_path_owner(directory, owner)

    def change_dir_owner(self, directory, owner):
        '''
        .. warning:: Deprecated. Please use :meth:`change_path_owner` instead. (Will be removed in 0.7.0)

        :param directory: Directory to change owner.
        :type directory: :class:`str`
        :param owner: User that should own this directory.
        :type owner: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.change_dir_owner(directory='/etc/my-path', owner='someuser')
        '''
        self.log('"change_dir_owner" is deprecated, please use "change_path_owner" instead.')
        self.change_path_owner(directory, owner)

    def change_file_owner(self, path, owner):
        '''
        .. warning:: Deprecated. Please use :meth:`change_path_owner` instead. (Will be removed in 0.7.0)

        :param path: Path of the file.
        :type path: :class:`str`
        :param owner: User that should own this file.
        :type owner: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.change_file_owner(path='/etc/init.d/someapp', owner='someuser')
        '''
        self.log('"change_file_owner" is deprecated, please use "change_path_owner" instead.')
        self.change_path_owner(path, owner)

    def change_path_owner(self, path, owner):
        '''
        Changes the owner of a given path. Please be advised that this method is recursive, so if the path is a directory, all contents of it will belong to the specified owner.

        :param path: Path to have its owner changed.
        :type path: :class:`str`
        :param owner: User that should own this path.
        :type owner: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.change_path_owner(path='/etc/my-path', owner='someuser')
        '''
        self.execute('chown -R %s %s' % (owner, path), stdout=False, sudo=True)

    def get_object_mode(self, path):
        '''
        Returns the permission mode of a given object. Raises IOError if the path doesn't exist.

        :param path: Path of the given object.
        :type path: :class:`str`

        :return: The path permission mode
        :rtype: :class:`int`

        :raise: :class:`IOError` if the path doesn't exist

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    if self.get_object_mode('/home/user/logs') == 644:
                        pass
        '''
        if not self.remote_exists(path) and not self.remote_exists_dir(path):
            raise IOError('The file at path %s does not exist' % path)
        return int(self.execute('stat -c %%a %s' % path, stdout=False, sudo=True))

    def change_path_mode(self, path, mode, recursive=False):
        '''
        Changes the mode of a given path.

        :param path: Path to have its mode changed.
        :type path: :class:`str`
        :param mode: Mode to change to.
        :type mode: :class:`int`
        :param recursive: Indicates if the mode of the objects in the path should be changed recursively. Defaults to :class:`False`.
        :type recursive: :class:`bool`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.change_path_mode(directory='/home/user/logs', mode=644, recursive=True)
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
        .. warning:: Deprecated. Please use :meth:`change_path_mode` instead. (Will be removed in 0.7.0)

        :param path: Path of the directory.
        :type path: :class:`str`
        :param mode: Mode of the directory.
        :type mode: :class:`int`
        :param recursive: Indicates if the mode of the objects in the path should be changed recursively. Defaults to :class:`False`.
        :type recursive: :class:`bool`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.change_dir_mode(directory='/home/user/logs',
                                         mode=644,
                                         recursive=True)
        '''
        self.change_path_mode(path, mode, recursive=recursive)

    def change_file_mode(self, path, mode):
        '''
        .. warning:: Deprecated. Please use :meth:`change_path_mode` instead. (Will be removed in 0.7.0)

        :param path: Path of the file.
        :type path: :class:`str`
        :param mode: Mode of the file.
        :type mode: :class:`int`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.change_file_mode(path='/etc/init.d/someapp',
                                          mode=777)
        '''
        self.change_path_mode(path, mode)

    def md5_local(self, path):
        '''
        Calculates an md5 hash for a given file in the local system. Returns :class:`None` if file does not exist.

        :param path: Path of the local file.
        :type path: :class:`str`

        :return: The hash generated, or :class:`None` if `path` doesn't exist.
        :rtype: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    hash = self.md5_local('/tmp/my-file')
        '''
        if not self.local_exists(path):
            return None

        result = self.execute_local(self.__md5_hash_command(path), stdout=False, sudo=True)
        return result.strip()

    def md5_remote(self, path):
        '''
        Calculates an md5 hash for a given file in the remote system. Returns :class:`None` if file does not exist.

        :param path: Path of the remote file.
        :type path: :class:`str`

        :return: The hash generated, or None if `path` doesn't exist.
        :rtype: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    hash = self.md5_remote('/tmp/my-file')
        '''
        if not self.remote_exists(path):
            return None

        result = self.execute(self.__md5_hash_command(path), stdout=False, sudo=True)
        return result.strip()

    def __md5_hash_command(self, path):
        return 'md5sum %s | cut -d " " -f 1' % path

    def remove_dir(self, path, sudo=False, recursive=False):
        '''
        Removes a directory in the remote server. Returns :data:`True` in the event of the directory actually been removed. :data:`False` otherwise.

        :param path: Path of the remote directory.
        :type path: :class:`str`
        :param sudo: Indicates whether the directory should be removed by the super-user. Defaults to :data:`False`.
        :type sudo: :class:`bool`
        :param recursive: Indicates whether the directory should be removed recursively or not. Defaults to :data:`False`.
        :type recursive: :class:`bool`

        :return: Whether the directory had to be removed or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.remove_dir('/tmp/my-dir', sudo=True, recursive=True)
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

    def remove_file(self, path, sudo=False, stdout=True):
        '''
        Removes a file in the remote server. Returns :data:`True` in the event
        of the file actually been removed. :data:`False` otherwise.

        :param path: Path of the remote file.
        :type path: :class:`str`
        :param sudo: Indicates whether the file should be removed by the
        super-user. Defaults to :data:`False`.
        :type sudo: :class:`bool`
        :param stdout: If :data:`False` we will suppress logging message.
         Defaults to :data:`True`.

        :return: Whether the file had to be removed or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.remove_file('/tmp/my-file', sudo=True)
        '''

        if self.remote_exists(path):
            self.execute('rm -f %s' % path, stdout=False, sudo=sudo)
            if stdout:
                self.log('%s removed!' % path)
            return True
        return False

    def replace_file(self, from_file, to_file):
        '''
        .. warning:: Deprecated. Please use :meth:`put_file` instead. (Will be removed in 0.7.0)

        :param from_file: Path in the local system.
        :type from_file: :class:`str`
        :param to_file: Path in the remote system.
        :type to_file: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.replace_file('/tmp/my-file', '/tmp/my-file')
        '''
        self.put_file(from_file, to_file)

    def remote_symlink(self, from_file, to_file, sudo=False):
        '''
        Creates a symlink in the remote server.

        :param from_file: Symlink source.
        :type from_file: :class:`str`
        :param to_file: Symlink target.
        :type to_file: :class:`str`
        :param sudo: Indicates whether the symlink should be created by the super-user. Defaults to :data:`False`.
        :type sudo: :class:`bool`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.remote_symlink('/home/user/my-app', '/etc/init.d/my-app', sudo=True)
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

    def put_file(self, from_file, to_file, sudo=False, stdout=True):
        '''
        Puts a file to the remote server.

        :param from_file: Source file in the local system.
        :type from_file: :class:`str`
        :param to_file: Target path in the remote server.
        :type to_file: :class:`str`
        :param sudo: Indicates whether the file should be created by the super-user. Defaults to :data:`False`.
        :type sudo: :class:`bool`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.put_file('/home/user/my-app', '/etc/init.d/my-app', sudo=True)
        '''

        with self.__showing_command_output(stdout):
            fabric.api.put(from_file, to_file, use_sudo=sudo)

    def update_file(self, from_file, to_file, owner=None, options={}, sudo=None):
        '''
        One of the most used methods in provy. This method renders a template, then if the contents differ from the remote server (or the file does not exist at the remote server), it sends the results there.

        Again, combining the parameters sudo and owner you can have files that belong to an user that is not a super-user in places that only a super-user can reach.

        Returns True if the file was updated, False otherwise.

        :param from_file: Template file in the local system.
        :type from_file: :class:`str`
        :param to_file: Target path in the remote server.
        :type to_file: :class:`str`
        :param owner: Owner for the file in the remote server.
        :type owner: :class:`str`
        :param options: Dictionary of options that can be used in the template.
        :type options: :class:`dict`
        :param sudo: Indicates whether the file should be created by the super-user. Defaults to :data:`None`.
        :type sudo: :class:`bool`

        :return: Whether the file was updated or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    self.update_file('/home/user/my-app', '/etc/init.d/my-app', owner='my-user',
                                     {
                                        'option_a': 1,
                                        'option_b': 2
                                     },
                                     sudo=True)
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

        :param text: Text to be written to the temp file.
        :type text: :class:`str`

        :return: Temp file path.
        :rtype: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    path = self.write_to_temp_file('some random text')
                    self.put_file(path, '/tmp/some-file')
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

        :param path: File path on the remote server.
        :type path: :class:`str`
        :param sudo: Indicates whether the file should be read by a super-user. Defaults to :data:`True`.
        :type sudo: :class:`bool`

        :return: The contents of the file.
        :rtype: :class:`str`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    last_update = self.read_remote_file('/tmp/last-update')
        '''
        result = self.execute_python("import codecs; print codecs.open('%s', 'r', 'utf-8').read()" % path, stdout=False, sudo=sudo)
        return result

    def render(self, template_file, options={}):
        '''
        Renders a template with the given options and returns the rendered text.
        The template_file parameter should be just the name of the file and not the file path. jinja2 will look for templates at the files directory in the provyfile path, as well as in the templates directory of any registered module (check the <em>register_template_loader</em> method).
        The options parameter will extend the server context, so all context variables (including per-server options) are available to the renderer.

        :param template_file: Template file path in the local system.
        :type template_file: :class:`str`
        :param options: Options to be passed to the template, as a dictionary. Defaults to empty :class:`dict`.
        :type options: :class:`dict`

        :return: The contents of the file.
        :rtype: :class:`str`

        Example:
        ::

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
        Returns :data:`True` if the given process is running (listed in the process listing), :data:`False` otherwise.

        :param process: Regular expression string that specifies the process name.
        :type process: :class:`str`
        :param sudo: Indicates if the process listing should be done by the super-user. Defaults to :data:`False`.
        :type sudo: :class:`bool`

        :return: Whether the process is running or not.
        :rtype: :class:`bool`

        Example:
        ::

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
        Returns :data:`True` if the given line of text is present in the given file. Returns :data:`False` otherwise (even if the file does not exist).

        :param line: Line of text to verify in the given file.
        :type line: :class:`str`
        :param file_path: Complete path of the remote file.
        :type file_path: :class:`str`

        :return: Whether the line exists or not.
        :rtype: :class:`bool`

        Example:
        ::

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

        :param line: Line of text to verify in the given file.
        :type line: :class:`str`
        :param file_path: Complete path of the remote file.
        :type file_path: :class:`str`
        :param owner: The user that owns the file. Defaults to :data:`None` (the context user is used in this case).
        :type owner: :class:`str`
        :param sudo: Indicates whether the file should be managed by the super-user. Defaults to :data:`False`.
        :type sudo: :class:`bool`

        Example:
        ::

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

        It returns a ContextManager object, so this is meant to go inside a `with` block.

        :param role: Role to be used.
        :type role: :class:`Role`

        Example:
        ::

            from provy.core import Role

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AptitudeRole) as role:
                        role.ensure_package_installed('nginx')
        '''
        return UsingRole(role, self.prov, self.context)

    def get_distro_info(self):
        '''
        Returns a :class:`DistroInfo` with valuable information regarding the distribution of the server.

        In the backgrounds, what it does is to run

        .. code-block:: sh

            $ lsb_release -a

        in the server, so you might want to check which results are usual for your distribution.

        Example:
        ::

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

    Refer to :meth:`Role.get_distro_info` usage.
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
