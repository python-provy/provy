# -*- coding: utf-8 -*-
from StringIO import StringIO
from contextlib import contextmanager
from copy import copy
from provy.core import Role
from provy.more.debian import AptitudeRole

import json

__author__ = 'jb'



class UwsgiSite(object):
    """
    Configuration for single debian uWsgiSite.


    """

    def __init__(self, parent, app_name):
        super(UwsgiSite, self).__init__()
        self.parent_role = parent
        self.python_version = "27"
        self.app_name = app_name
        self.uwsgi_params = {}
        self.final_config = {}


    def add_uwsgi_config_params(self, update_from_context = False, **kwargs):
        """
            Adds configuration params to context.

            :param kwargs: args to add
            :param update_from_context: If true will update values of passed parameters


            Updating from context
            =====================

            It is possible to update keys from context. You can provide configuration keys that contain context variable names
            *in syntax of str.format function*, that is that look like that: "{wsgi_module}:application".


        """
        params = copy(kwargs)
        if update_from_context:
            self.update_dict_from_context(params)
        self.uwsgi_params.update(params)

    @property
    def context(self):
        """
            Returns parent's context
        """
        return self.parent_role.context

    def update_dict_from_context(self, updated_dict):
        dict = {
            "app_name" : self.app_name,
        }

        dict.update(self.context)

        for k in updated_dict.iterkeys():
            if isinstance(updated_dict[k], basestring):
                try:
                    updated_dict[k] = updated_dict[k].format(**dict)
                except KeyError:
                    pass

    def default(self):
        """
            Returns dictionary of default configuration.
        """

        defaults = {
            "chdir" : "{django_project_root}",
            "module" : "{django_wsgi_module}:application",

        }

        if self.python_version[0] == '2':
            defaults["plugin"] =  ["python" + self.python_version]

        self.update_dict_from_context(defaults)

        to_delete = []
        for k, v in defaults.iteritems():
            if "{" in v:
                to_delete.append(k)

        for k in to_delete:
            del defaults[k]

        return defaults

    def ensure_config_file(self, override = True, enable = True, **kwargs):
        """
            Writes uWsgi config file in json format.

            :param override: If true will update existing settins.
            :param enable: If true application will be enabled.
            :param kwargs: Additional for config file.

        """
        app_config_file = self.parent_role.is_app_avilable(self.app_name)
        if not override and app_config_file:
            raise ValueError("Can't override site {}".format(app_config_file))

        settings_dict = {}
        settings_dict.update(self.uwsgi_params)
        settings_dict.update(kwargs)

        settings = json.dumps({"uwsgi" : settings_dict})

        self.parent_role.put_file(StringIO(settings), "/etc/uwsgi/apps-available/{}.json".format(self.app_name), sudo=True)

        if enable:
            self.parent_role.ensure_app_enabled(self.app_name)

        self.check_debian_settings(settings)

        self.final_config = settings

    def check_debian_settings(self, settings):
        """
            Checks if overriden settings that may do more harm than good.
        """
        if any(map(lambda x : x in settings, ["uid", "gid", "socket", "pid"])):
            import warnings
            warnings.warn("You have set one of {} settings for uwsi. If you are configuring packaged uwsgi you might "
                          "have problems. These settings have defaults set by debian and some parts of system may "
                          "depend on it!")

    def restart(self):
        self.parent_role.restart_wsgi()

    @property
    def socket(self):
        """
            Read-only property returnig *default* socket location in packaged uWsgi.
        """
        return "/var/run/uwsgi/app/{}/socket".format(self.app_name)



class UwsgiRole(Role):

    """
        Role that adds support for uwsgi.

        Example usage::

           with uwsgi("lfitj_app") as app:

                app.ensure_config_file(
                    apply_defaults=False,
                    virtualenv = venv.env_dir(VIRTUAL_ENV_NAME),
                    chdir = CMS_ROOT_DIR,
                    pythonpath = [CMS_ROOT_DIR],
                    plugins = ['python27'],
                    module = "wsgi:application"
                )

                with self.using(VirtualenvRole) as venv:
                    self.change_dir_mode(venv.env_dir(CMS_ROOT_DIR_PARENT), 555, True)

                app.restart()
    """

    def install_uwsgi(self):
        with self.using(AptitudeRole) as role:
            role.ensure_up_to_date()
            role.ensure_package_installed("uwsgi-extra")

    @contextmanager
    def __call__(self, site_name, language = "python"):
        if language == "python":
            with self.using(AptitudeRole) as apt:
                apt.ensure_package_installed("uwsgi-plugin-python")

        yield UwsgiSite(self, site_name)

    def provision(self):
        super(UwsgiRole, self).provision()
        self.install_uwsgi()

    def is_app_avilable(self, app):
        sites = self.remote_list_directory("/etc/uwsgi/apps-available/")
        return self._app_in_list(app, sites)

    def is_app_enabled(self, app):
        sites = self .remote_list_directory("/etc/uwsgi/apps-enabled/")
        return self._app_in_list(app, sites)

    def restart_wsgi(self):
        self.execute("service uwsgi restart", sudo=True)

    def ensure_app_enabled(self, app):
        config_file = self.is_app_avilable(app)
        if not config_file:
            raise ValueError("Cant enable uwsgi app if it is not avilable (not in apps-available")
        if not self.is_app_enabled(app):
            self.execute("ln -s  /etc/uwsgi/apps-available/{config_file} /etc/uwsgi/apps-enabled/{config_file}".format(config_file = config_file), sudo=True)
        self.restart_wsgi()

    def ensure_app_disabled(self, app):
        config_file = self.is_app_enabled(app)
        if config_file:
            self.execute("unlink /etc/uwsgi/apps-enabled/{config_file}".format(config_file = config_file), sudo=True)
        self.restart_wsgi()

    def remove_config_file(self, app):
        self.ensure_app_disabled(app)
        config_file = self.is_app_avilable(app)
        if config_file:
            self.remove_file(config_file)


    def _app_in_list(self, site, sites):
        for ext in ("json", "ini", "xml", "yaml"):
            s = ".".join((site, ext))
            if s in sites:
                return s
