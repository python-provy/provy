__author__ = 'jb'

from os import path

from provy.core import Role

class Dpkg(Role):


    def install_file(self, local_file):
        file_name = path.abspath(local_file).rsplit("/", 1)
        temp_dir = self.
