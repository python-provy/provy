#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Git repository creation operations within CentOS distributions.
'''

from provy.core import Role
from provy.more.centos.package.yum import YumRole


class GitRole(Role):
    '''
    This role provides utility methods for Git repositories management within CentOS distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.centos import GitRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(GitRole) as role:
                role.ensure_repository('git://github.com/heynemann/provy.git',
                                       '/home/user/provy',
                                       owner='user',
                                       branch='some-branch')
    </pre>
    '''

    def provision(self):
        '''
        Installs git dependencies. This method should be called upon if overriden in base classes, or Git won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import GitRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(GitRole) # does not need to be called if using with block.
        </pre>
        '''
        with self.using(YumRole) as role:
            role.ensure_up_to_date()
            role.ensure_package_installed('git-core')

    def ensure_repository(self, repo, path, owner=None, branch=None):
        '''
        Makes sure the repository is create in the remote server. This method does not update the repository or perform any operations in it. It is merely used to ensure that the repository exists in the specified path.
        <em>Parameters</em>
        repo - Git repository url.
        path - Path to create the local repository.
        owner - User that owns the repository directory.
        branch - If specified, the given branch will be checked-out, otherwise it stays in the master branch.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.centos import GitRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(GitRole) as role:
                    role.ensure_repository('git://github.com/heynemann/provy.git',
                                           '/home/user/provy',
                                           owner='user',
                                           branch='some-branch')
        </pre>
        '''
        if not self.remote_exists_dir(path):
            self.log("Repository for %s does not exist! Cloning..." % repo)
            self.execute("git clone %s %s" % (repo, path),
                         sudo=True,
                         stdout=False)
            self.log("Repository %s cloned!" % repo)

        branch_name = "# On branch %s" % branch
        if branch and not branch_name in self.execute("git --git-dir=\"%s/.git\" --work-tree=\"%s\" status" % (path, path),
                sudo=True, stdout=False):
            self.log("Repository for %s is not in branch %s ! Switching..." % (repo, branch))
            self.execute("git --git-dir=\"%s/.git\" --work-tree=\"%s\" checkout %s" % (path, path, branch))
            self.log("Repository %s currently in branch %s!" % (repo, branch))

        if owner:
            self.change_dir_owner(path, owner)
