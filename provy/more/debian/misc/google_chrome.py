from provy.more.debian import AptitudeRole

__author__ = 'jb'

from provy.core import Role

class ChromeRole(Role):

    def provision(self):
        super(ChromeRole, self).provision()

        with self.using(AptitudeRole) as role:
            if not role.is_package_installed("google-chrome-stable"):
                role.ensure_gpg_key("https://dl-ssl.google.com/linux/linux_signing_key.pub")
                role.ensure_aptitude_source("deb http://dl.google.com/linux/deb/ stable main")
                role.force_update()
                role.ensure_package_installed("google-chrome-stable")

