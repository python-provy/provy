from provy.core import Role


class MOTDRole(Role):
    """
        Role that updates system message of the day.
    """
    def install_motd(self, message_of_the_day):
        self.put_file(message_of_the_day, "/etc/motd", sudo=True)
        self.change_file_mode("/etc/motd", 644)

def InstallMOTD(motd):
    """
        Creates role that will install MOTD passed as parameter.
    """
    class InstallMotdRole(Role):
        def provision(self):
            with self.using(MOTDRole) as role:
                role.install_motd(motd)
    return InstallMotdRole
