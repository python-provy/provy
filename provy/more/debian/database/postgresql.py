#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide `PostgreSQL <http://www.postgresql.org/>`_ database management utilities for Debian distributions.
'''
from StringIO import StringIO
from provy.more.base.database.postgresql import BasePostgreSQLRole
from provy.more.debian.package.aptitude import AptitudeRole


class PostgreSQLRole(BasePostgreSQLRole):
    '''
    This role provides `PostgreSQL <http://www.postgresql.org/>`_ database management utilities for Debian distributions.

    Take a look at :class:`provy.more.base.database.postgresql.BasePostgreSQLRole` for more available methods.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import PostgreSQLRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(PostgreSQLRole) as role:
                    role.ensure_user("john")
                    role.ensure_database("foo", owner="john")
    '''
    def provision(self):
        '''
        Installs `PostgreSQL <http://www.postgresql.org/>`_ and its dependencies.
        This method should be called upon if overriden in base classes, or PostgreSQL won't work properly in the remote server.

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(PostgreSQLRole) # no need to call this if using with block.
        '''
        with self.using(AptitudeRole) as role:
            role.ensure_package_installed('postgresql')
            role.ensure_package_installed('postgresql-server-dev-%s' % self.__get_version())

    def __get_version(self):
        distro = self.get_distro_info()
        if distro.distributor_id.lower() == 'ubuntu':
            version = '9.1'
        else:
            version = '8.4'
        return version

class PostgresqlFromPostgresqlRepo(BasePostgreSQLRole):
    """
    Installs `PostgreSQL <http://www.postgresql.org/>`_
    and its dependencies. Postgresql is installed from repository
    maintained by `postgresql.org <https://wiki.postgresql.org/wiki/Apt>`_.
    """

    _DEB_LINE = """deb http://apt.postgresql.org/pub/repos/apt/ {codename}-pgdg main"""

    _POSTGRE_VER = "9.2"

    _MAIN_INSTALLED_PACKAGE = "postgresql-{ver}"

    @property
    def package(self):
        return self._MAIN_INSTALLED_PACKAGE.format(ver = self._POSTGRE_VER)

    def provision(self):
        """
        Installs `PostgreSQL <http://www.postgresql.org/>`_
        and its dependencies. Postgresql is installed from repository
        maintained by `postgresql.org <https://wiki.postgresql.org/wiki/Apt>`_.

        This method should be called upon if overriden in base classes,
        or PostgreSQL won't work properly in the remote server.

        :see:`PostgreSQLRole`
        """
        with self.using(AptitudeRole) as role:
            self.register_template_loader("provy.more.debian.database")
            role.ensure_gpg_key(file = StringIO(self.render("ACCC4CF8.asc")))

            role.ensure_aptitude_source(
                self._DEB_LINE.format(codename = self.get_distro_info().codename)
            )

            role.override_preferences_file("pgdg",
                                           StringIO(self.render("pgdg.conf")))

            role.force_update()

            # role.ensure_package_installed("libpq5")
            # role.ensure_package_installed("postgresql-client")
            role.ensure_package_installed("postgresql-9.2")

def create_postgres_role(postgres_version):
    """
    Creates subclass of :class:`PostgresqlFromPostgresqlRepo` role that installs
    specific version of the database server.

    :param postgres_version: Version to install, for example `"9.2"`.
    """

    class SpecificPsqlRole(PostgresqlFromPostgresqlRepo):

        _POSTGRE_VER = postgres_version

    return SpecificPsqlRole
