#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide `Ruby <http://www.ruby-lang.org/>`_ utility methods for Debian distributions.
'''

from provy.core import Role
from provy.more.debian import AptitudeRole


UPDATE_ALTERNATIVES_COMMAND = """
update-alternatives --force --install /usr/bin/ruby ruby /usr/bin/ruby{version} {priority} \
  --slave   /usr/share/man/man1/ruby.1.gz ruby.1.gz /usr/share/man/man1/ruby{version}.1.gz \
  --slave   /usr/bin/ri ri /usr/bin/ri{version} \
  --slave   /usr/share/man/man1/ri.1.gz ri.1.gz /usr/share/man/man1/ri{version}.1.gz \
  --slave   /usr/bin/irb irb /usr/bin/irb{version} \
  --slave   /usr/share/man/man1/irb.1.gz irb.1.gz /usr/share/man/man1/irb{version}.1.gz \
  --slave   /usr/bin/erb erb /usr/bin/erb{version} \
  --slave   /usr/share/man/man1/erb.1.gz erb.1.gz /usr/share/man/man1/erb{version}.1.gz \
  --slave   /usr/bin/rdoc rdoc /usr/bin/rdoc{version} \
  --slave   /usr/share/man/man1/rdoc.1.gz rdoc.1.gz /usr/share/man/man1/rdoc{version}.1.gz \
  --slave   /usr/bin/testrb testrb /usr/bin/testrb{version} \
  --slave   /usr/share/man/man1/testrb.1.gz testrb.1.gz /usr/share/man/man1/testrb{version}.1.gz
"""


class RubyRole(Role):
    '''
    This role provides `Ruby <http://www.ruby-lang.org/>`_ utilities for Debian distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import RubyRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(RubyRole)
    '''

    version = '1.9.1'
    priority = 400

    def provision(self):
        '''
        Installs `Ruby <http://www.ruby-lang.org/>`_ and its dependencies.
        This method should be called upon if overriden in base classes, or Ruby won't work properly in the remote server.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import RubyRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(RubyRole) # no need to call this if using with block.
        '''
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('ruby{version}-full'.format(version=self.version))

            update_alternatives_command = UPDATE_ALTERNATIVES_COMMAND.format(
                version=self.version,
                priority=self.priority,
            )
            self.execute(update_alternatives_command, sudo=True)
