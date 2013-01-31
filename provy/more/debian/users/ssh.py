#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide SSH keygen utilities for Debian distributions.
'''

from os.path import join
import base64
import StringIO
from Crypto.PublicKey import RSA


from provy.core import Role


class SSHRole(Role):
    '''
    This role provides SSH keygen utilities for Debian distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import SSHRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SSHRole) as role:
                    role.ensure_ssh_key(user='someuser', private_key_file="private-key")
    '''

    def ensure_ssh_dir(self, user):
        """
        Creates user ssh directory for `user`, and sets proper permissions.
        :param user: User for which to create remote directory.

        :return: ssh directory for `user`.
        """
        path = "/home/{}/.ssh".format(user)
        self.ensure_dir(path, sudo=True, owner=user)
        self.change_path_mode(path, 700, recursive=True)
        self.change_path_owner(path, "{0}:{0}".format(user))
        return path

    def override_authorized_keys(self, user, authorized_key_file):
        """
        Overrides `user`'s authorized keys file.

        :param user:  Name of ser for which to perform action. :type user:`str`.
        :param authorized_key_file: Either a file like object containing keys
        or an iterable of file names containing public keys.
        """
        if isinstance(authorized_key_file, (list, set, tuple)):
            file = StringIO.StringIO()
            for key in authorized_key_file:
                with open(key) as read_file:
                    file.write(read_file.read().strip())
                    file.write("\n")
            authorized_key_file = file

        path = self.ensure_ssh_dir(user)
        file_path = path + "/authorized_keys"
        self.put_file(authorized_key_file, file_path, sudo=True)
        self.ensure_ssh_dir(user) #as a side effect forces 700 perms

    def override_known_hosts(self, user, known_hosts_file):
        """
        Overrides known hosts file for  user.

        :param user:  Name of ser for which to perform action. :type user:`str`.
        :param known_hosts_file: Path to known hosts file to upload.
        """
        path = self.ensure_ssh_dir(user)
        file_path = path + "/known_hosts"
        self.update_file(known_hosts_file, file_path, owner=user, sudo=True)
        self.execute("chmod -R og-rwx {}".format(path), sudo=True)
        self.ensure_ssh_dir(user) #as a side effect forces 700 perms

    def ensure_ssh_key(self, user, private_key_file):
        '''
        Ensures that the specified private ssh key is present in the remote server. Also creates the public key for this private key.

        The private key file must be a template and be accessible to the :meth:`Role.render <provy.core.roles.Role.render>` method.

        :param user: Owner of the keys.
        :type user: :class:`str`
        :param private_key_file: Template file for the private key.
        :type private_key_file: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import SSHRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(SSHRole) as role:
                        role.ensure_ssh_key(user='someuser', private_key_file="private-key")

        '''
        path = '/home/%s' % user
        ssh_path = join(path, '.ssh')
        self.ensure_dir(ssh_path, sudo=True, owner=user)
        private_key = self.render(private_key_file)

        key = RSA.importKey(private_key)
        public_key = key.publickey().exportKey(format='OpenSSH')

        self.__write_keys(user, private_key, public_key)

    def __write_keys(self, user, private_key, public_key):
        path = '/home/%s' % user
        ssh_path = join(path, '.ssh')
        pub_path = join(ssh_path, 'id_rsa.pub')
        priv_path = join(ssh_path, 'id_rsa')

        host = self.execute_python('import os; print os.uname()[1]', stdout=False)
        host_str = "%s@%s" % (user, host)

        pub_text = "%s %s" % (public_key, host_str)
        pub_file = self.write_to_temp_file(pub_text)
        priv_file = self.write_to_temp_file(private_key)
        result_pub = self.update_file(pub_file, pub_path, sudo=True, owner=user)
        result_priv = self.update_file(priv_file, priv_path, sudo=True, owner=user)

        if result_pub or result_priv:
            self.log("SSH keys generated at server!")
            self.log("Public key:")
            self.log(pub_text)
