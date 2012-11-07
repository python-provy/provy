__author__ = 'jb'

from provy.core import Role

class DpkgRole(Role):

    def install_file(self, local_file):

        file_name = local_file.rsplit("/", 1)[1]
        temp_dir = self.create_temp_dir()
        self.put_file(local_file, temp_dir + "/" + file_name)
        self.execute("dpkg -i {}".format(file_name), cwd = temp_dir)

