from contextlib import contextmanager
from provy.core import Role
from provy.more.debian.package.alternatives import AlternativesRole


class _Installer(object):
    """
        Internal class that actually performs installation.
    """
    def __init__(self, parent, java_package_file, target_dir=None):
        super(_Installer, self).__init__()
        self.file = java_package_file
        self.target_dir = target_dir
        self.parent = parent

    def install(self):
        """
            Performs actual installation of java on remote server.
        """
        temp_dir = self.parent.create_remote_temp_dir()
        remote_zip_file = "java.tar.gz"
        self.parent.put_file(self.file, temp_dir + "/" + remote_zip_file, stdout=False)
        self.parent.execute("tar -zxf {}".format(remote_zip_file), cwd=temp_dir, stdout=False)
        result = filter(lambda x: "jdk" in x, self.parent.remote_list_directory(temp_dir))
        assert len(result) == 1
        if self.target_dir is None:
            self.target_dir = "/opt/" + result[0]
        self.parent.remove_dir(self.target_dir, sudo=True, recursive=True)
        self.parent.execute("mv {} {}".format(result[0], self.target_dir), cwd=temp_dir, sudo=True)

    def add_alternative(self, set_as_default=True):
        """
            Adds installed java to alternatives system
        """
        # TODO: Add other alternatives like javac
        with self.parent.using(AlternativesRole) as alt:
            alt.add_alternative("java", self.target_dir + "/jre/bin/java",
                                set_as_default=set_as_default,
                                path_to_link="/usr/bin/java")


class OracleJavaRole(Role):
    """
        Installs Oracle Java from locally installed package.
    """
    @contextmanager
    def __call__(self, java_package_file, target_dir=None):
        yield _Installer(self, java_package_file, target_dir)


def InstallJavaFrom(java_package_file, target_dir=None, set_as_default=True):
    """
        Creates a role that installs oracle java from locally installed package
        file in tar.gz format. tar.gz should be downloaded from oracle site.

        servers = {
            'new': {
                'address': '192.168.57.20',
                'user': USERNAME,
                'roles': [
                    InstallJavaFrom('path_to_file_on_local_machine')
                ]
                }
            }
        }

    """
    class OracleJavaInstallerRole(OracleJavaRole):
        def provision(self):
            with self.using(OracleJavaRole) as role:
                with role(java_package_file, target_dir) as installer:
                    installer.install()
                    installer.add_alternative(set_as_default)
    return OracleJavaInstallerRole
