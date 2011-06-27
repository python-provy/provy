#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole

class GitRole(Role):
    def provision(self):
        self.use(AptitudeRole).ensure_up_to_date()
        self.use(AptitudeRole).ensure_package_installed('git-core')

    def ensure_repository(self, repo, path, owner=None):
        if not self.remote_exists_dir(path):
            self.log("Repository for %s does not exist! Cloning..." % repo)
            self.execute("git clone %s %s" % (repo, path), sudo=True, stdout=False)
            self.log("Repository %s cloned!" % repo)

        if owner:
            self.change_dir_owner(path, owner)
