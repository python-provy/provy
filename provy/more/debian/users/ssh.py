#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import join
import base64
import M2Crypto.RSA

from provy.core import Role

class SSHRole(Role):
    def ensure_ssh_key(self, user, private_key_file):
        path = '/home/%s' % user
        ssh_path = join(path, '.ssh')
        self.ensure_dir(ssh_path, sudo=True, owner=user)
 
        private_key = open(self.local_file(private_key_file)).read()
        key = M2Crypto.RSA.load_key_string(private_key)
        public_key = 'ssh-rsa %s' % (base64.b64encode('\0\0\0\7ssh-rsa%s%s' % key.pub()))

        self.write_keys(user, private_key, public_key)

    def generate_ssh_key(self, user):
        path = '/home/%s' % user
        ssh_path = join(path, '.ssh')
        self.ensure_dir(ssh_path, sudo=True, owner=user)
        priv_path = join(ssh_path, 'id_rsa')

        if self.remote_exists(priv_path):
            return

        keypair = self.generate_key_pair()
        pub, priv = keypair['public'], keypair['private']
        self.write_keys(user, priv, pub)

    def write_keys(self, user, private_key, public_key):
        path = '/home/%s' % user
        ssh_path = join(path, '.ssh')
        pub_path = join(ssh_path, 'id_rsa.pub')
        priv_path = join(ssh_path, 'id_rsa')

        host = self.execute_python('import os; print os.uname()[1]', stdout=False)
        host_str = "%s@%s" % (user, host)

        pub_text = "%s %s" % (public_key, host_str)
        pub_file = self.write_to_temp_file(pub_text)
        priv_file = self.write_to_temp_file("""-----BEGIN RSA PRIVATE KEY-----
%s
-----END RSA PRIVATE KEY-----""" % private_key)
        self.update_file(pub_file, pub_path, sudo=True, owner=user)
        self.update_file(priv_file, priv_path, sudo=True, owner=user)

        self.log("SSH keys generated at server!")
        self.log("Public key:")
        self.log(pub_text)

    def generate_key_pair(self, bits=4096, exponent=65537):
        key = M2Crypto.RSA.gen_key(int(bits), int(exponent))
        priv_key = M2Crypto.RSA.BIO.MemoryBuffer()
        key.save_key_bio(priv_key, cipher=None)

        # The four bytes before 'ssh-rsa' define the Type (0) and Length (7) of the
        # 'ssh-rsa' string. This is part of TLV encoding used in BER.
        pub_key = 'ssh-rsa %s' % (base64.b64encode('\0\0\0\7ssh-rsa%s%s' % key.pub()))
        return {'bits': bits, 'public': pub_key, 'private': priv_key.read_all()}
