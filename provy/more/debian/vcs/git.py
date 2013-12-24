#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide `Git <http://git-scm.com/>`_ repository creation operations within Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class GitRole(Role):
    '''
    This role provides utility methods for `Git <http://git-scm.com/>`_ repositories management within Debian distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import GitRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(GitRole) as role:
                    role.ensure_repository('git://github.com/python-provy/provy.git', '/home/user/provy',
                                           owner='user', branch='some-branch')
    '''

    def provision(self):
        '''
        Installs `Git <http://git-scm.com/>`_ dependencies.
        This method should be called upon if overriden in base classes, or `Git <http://git-scm.com/>`_ won't work properly in the remote server.

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(GitRole) # does not need to be called if using with block.
        '''
        with self.using(AptitudeRole) as role:
            role.ensure_up_to_date()
            role.ensure_package_installed('git-core')

    def ensure_repository(self, repo, path, owner=None, branch=None, sudo=True):
        '''
        Makes sure the repository is create in the remote server.
        This method does not update the repository or perform any operations in it. It is merely used to ensure that the repository exists in the specified path.

        :param repo: Git repository url.
        :type repo: :class:`str`
        :param path: Path to create the local repository.
        :type path: :class:`str`
        :param owner: User that owns the repository directory. Defaults to :data:`None`, using the current one in the remote server.
        :type owner: :class:`str`
        :param branch: If specified, the given branch will be checked-out, otherwise it stays in the master branch.
        :type branch: :class:`str`
        :param sudo: If :data:`False`, won't sudo when creating the repository. Defaults to :data:`True`.
        :type sudo: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import GitRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(GitRole) as role:
                        role.ensure_repository('git://github.com/python-provy/provy.git', '/home/user/provy',
                                               owner='user', branch='some-branch')
        '''
        self.__clone_repository(path, repo, sudo, owner)
        self.__checkout_branch(branch, path, repo, sudo, owner)
        self.__normalize_ownership(owner, path)

    def __normalize_ownership(self, owner, path):
        if owner:
            self.change_path_owner(path, owner)

    def __checkout_branch(self, branch, path, repo, sudo, owner):
        branch_name = "# On branch %s" % branch
        if branch and not branch_name in self.execute("git --git-dir=\"%s/.git\" --work-tree=\"%s\" status" % (path, path),
                                                      sudo=True, stdout=False):
            self.log("Repository for %s is not in branch %s ! Switching..." % (repo, branch))
            self.execute('git --git-dir="%s/.git" --work-tree="%s" checkout %s' % (path, path, branch), sudo=sudo, user=owner)
            self.log("Repository %s currently in branch %s!" % (repo, branch))

    def __clone_repository(self, path, repo, sudo, owner):
        if not self.remote_exists_dir(path):
            self.log("Repository for %s does not exist! Cloning..." % repo)
            self.execute("git clone %s %s" % (repo, path), sudo=sudo, stdout=False, user=owner)
            self.log("Repository %s cloned!" % repo)
