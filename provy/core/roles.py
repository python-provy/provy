#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from os.path import exists, join, split
from datetime import datetime
from tempfile import gettempdir, NamedTemporaryFile
from hashlib import md5

from fabric.api import run, put, settings, hide
from fabric.api import sudo as fab_sudo
from jinja2 import Template

class Role(object):
    def __init__(self, prov, context):
        self.prov = prov
        self.context = context

    def log(self, msg):
        print '[%s] %s' % (datetime.now().strftime('%H:%M:%S'), msg)

    def provision(self):
        pass

    def cleanup(self):
        pass

    def execute(self, command, stdout=True, sudo=False):
        func = sudo and fab_sudo or run
        if stdout:
            return func(command)

        with settings(
            hide('warnings', 'running', 'stdout', 'stderr')
        ):
            return func(command)

    def execute_python(self, command, stdout=True):
        return self.execute('''python -c "%s"''' % command, stdout)

    def local_exists(self, file_path):
        return exists(file_path)

    def remote_exists(self, file_path):
        return self.execute('test -f %s; echo $?' % file_path, stdout=False) == '0'

    def remote_exists_dir(self, file_path):
        return self.execute('test -d %s; echo $?' % file_path, stdout=False) == '0'

    def local_temp_dir(self):
        return gettempdir()

    def remote_temp_dir(self):
        return self.execute_python('from tempfile import gettempdir; print gettempdir()', stdout=False)

    def md5_local(self, file_path):
        return md5(open(file_path).read()).hexdigest()

    def md5_remote(self, file_path):
        command = "from hashlib import md5; print md5(open('%s').read()).hexdigest()" % file_path
        return self.execute_python(command, stdout=False)

    def local_file(self, file_path):
        return join(self.context['abspath'], 'files', file_path)

    def remove_file(self, file_path, sudo=False):
        if self.remote_exists(file_path):
            self.log('File %s found at %s. Removing it...' % (file_path, self.context['host']))
            command = 'rm -f %s' % file_path
            self.execute(command, stdout=False, sudo=sudo)
            self.log('%s removed!' % file_path)
            return True
        return False

    def replace_file(self, from_file, to_file):
        put(from_file, to_file)

    def remote_symlink(self, from_file, to_file, sudo=False):
        command = 'ln -sf %s %s' % (from_file, to_file)
        if self.remote_exists(to_file):
            result = self.execute('ls -la %s' % to_file, stdout=False, sudo=sudo)
            if '->' in result:
                path = result.split('->')[-1].strip()
                if path != from_file:
                    self.log('Symlink has different path(%s). Syncing...' % path)
                    self.execute(command, stdout=False, sudo=sudo)
                    return True
        else:
            self.log('Symlink not found at %s! Creating...' % from_file)
            self.execute(command, stdout=False, sudo=sudo)
            return True

        return False

    def put_file(self, from_file, to_file, options={}, sudo=False):
        if sudo:
            temp_path = join(self.remote_temp_dir(), split(from_file)[-1])
            put(from_file, temp_path)
            self.execute('cp %s %s' % (temp_path, to_file), stdout=False, sudo=True)
            return

        put(from_file, to_file)

    def update_file(self, from_file, to_file, options={}, sudo=False):
        if not self.local_exists(from_file):
            raise RuntimeError('File does not exist locally at %s' % from_file)

        local_temp_path = None
        try:
            template = self.render(from_file, options)

            with NamedTemporaryFile(delete=False) as f:
                f.write(template)
                local_temp_path = f.name

            if not self.remote_exists(to_file):
                self.log('Remote file not found! Copying %s to server %s!' % (from_file, self.context['host']))
                self.put_file(local_temp_path, to_file, options, sudo)
                return True

            from_md5 = self.md5_local(local_temp_path)
            to_md5 = self.md5_remote(to_file)
            if from_md5.strip() != to_md5.strip():
                self.log('Hashes differ %s => %s! Copying %s to server %s!' % (from_md5, to_md5, from_file, self.context['host']))
                self.put_file(local_temp_path, to_file, options, sudo)
                return True
        finally:
            if exists(local_temp_path):
                os.remove(local_temp_path)

        return False

    def read_remote_file(self, file_path, sudo=False):
        return self.execute('cat %s' % file_path, stdout=False, sudo=sudo)

    def render(self, template_file, options):
        template = Template(open(template_file).read())
        return template.render(**options)
