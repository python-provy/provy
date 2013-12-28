# -*- coding: utf-8 -*-
from provy.more.debian.files.synchronize import RsyncSynchronize, VersionSynchronizeRole

class SyncFile(RsyncSynchronize):
    def provision(self):
        super(SyncFile, self).provision()
        self.synchronize_path('local', "/tmp/test-rsync", debug=True)

class VersionSync(VersionSynchronizeRole):

    def provision(self):
        super(VersionSync, self).provision()
        self.synchronize_path(1, 'local', "/tmp/test-version", debug=True)


servers = {
    'test': {
        'jb': {
            'address': '192.168.56.90',
            'user': 'jb',
            'roles': [SyncFile, VersionSync]
        }
    },
    "prod": {}
}