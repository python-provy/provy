#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import math

from provy.core import Role, AskFor
from provy.more.debian import UserRole, NPMRole

class LogIOServerRole(Role):
    def provision(self):
        version = '0.6.17'
        #self.register_template_loader('provy.logging.logio')

        if not self.is_process_running('log-server'):
            with self.using(NPMRole) as role:
                role.ensure_package_installed('socket.io', version)
                role.ensure_package_installed('connect')
                role.ensure_package_installed('underscore')

            self.__fix_socket_io_client(version)
            self.__clone_log_io()

            self.execute('cd /tmp/log.io/bin && ./configure && ./install/server', stdout=False, sudo=True)

        result = self.update_file('log.io.server.init.template',
                                  '/etc/init.d/log.io-server',
                                  sudo=True)
        if result:
            self.execute('chmod +x /etc/init.d/log.io-server', stdout=False, sudo=True)
            self.execute('update-rc.d log.io-server defaults', stdout=False, sudo=True)

            self.restart_server()


    def __fix_socket_io_client(self, version):
        if not self.remote_exists_dir('/usr/local/lib/node_modules/Socket.io-node-client'):
            self.execute('cd /usr/local/lib/node_modules/ && git clone git://github.com/msmathers/Socket.io-node-client.git', sudo=True, stdout=False)
            self.execute('cd /usr/local/lib/node_modules/Socket.io-node-client && git submodule update --init --recursive', sudo=True, stdout=False)
        self.execute('cd /usr/local/lib/node_modules/Socket.io-node-client/socket.io-node && sudo git checkout 0.6.17', sudo=True, stdout=False)

    def restart_server(self):
        attempts = 0

        self.execute('/etc/init.d/log.io-server stop', stdout=True, sudo=True)
        while attempts == 0 or (not self.is_process_running('log-server') and attempts < 10):
            timeout = math.pow(2, attempts)
            print "Waiting %d seconds for log-server to start" % timeout
            self.execute('/etc/init.d/log.io-server start', stdout=True, sudo=True)
            time.sleep(timeout)
            attempts += 1
        self.log("log.io server restarted!")

    def start_server(self):
        self.execute('/etc/init.d/log.io-server start', stdout=True, sudo=True)

    def stop_server(self):
        self.execute('/etc/init.d/log.io-server stop', stdout=True, sudo=True)

    def __clone_log_io(self):
        if not self.remote_exists_dir('/tmp/log.io'):
            self.execute('cd /tmp && git clone git://github.com/NarrativeScience/Log.io.git log.io', stdout=False)

    def ensure_config(self, port, authenticated=False, auth_user=None, auth_pass=None, owner=None):
        if not owner:
            owner = self.context['owner']

        self.ensure_dir('/etc/log.io', sudo=True, owner=owner)

        result = self.update_file('logio.server.conf.template',
                                 '/etc/log.io/server.conf',
                                 options={
                                     'port': port,
                                     'authenticated': authenticated,
                                     'auth_user': auth_user,
                                     'auth_pass': auth_pass
                                 },
                                 owner=owner,
                                 sudo=True)
        if result:
            self.restart_server()

class Server(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('timehome', identified_by=self.context['logio-pass'], is_admin=True)

        with self.using(LogIOServerRole) as role:
            role.ensure_config(port=9000, authenticated=False, auth_user='timehome', auth_pass=self.context['logio-pass'])


servers = {
    'test': {
        'server': {
            'address': '33.33.33.33',
            'user': 'vagrant',
            'roles': [
                Server
            ],
            'options': {
                'logio-pass': AskFor('logio-pass', 'Please enter the password for the log.io user')
            }
        }
    }
}
