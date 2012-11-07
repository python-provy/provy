__author__ = 'jb'

from provy.core import Role


class SudoRole(Role):

    """

    """

    def _upload_sudoers(self, local_file):
        tmpdir = self.create_temp_dir()
        self.change_dir_owner(tmpdir, "root")
        self.change_dir_mode(tmpdir, 440)
        remote_name = tmpdir + "/sudoers"
        self.put_file(local_file, remote_name, sudo=True, stdout=False)
        return remote_name

    def check_sudoers(self, local_file):
        remote_name = self._upload_sudoers(local_file)
        self.execute("visudo -c -f {}".format(remote_name), sudo=True, stdout=False)
        return remote_name

    def upload_sudoers(self, local_file):
        remote_name = self.check_sudoers(local_file)
        self.execute("mv {} /etc/sudoers && chmod 440 /etc/sudoers && chown root:root /etc/sudoers".format(remote_name), sudo=True)




