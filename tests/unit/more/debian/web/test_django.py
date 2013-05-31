from mock import call, MagicMock
from nose.tools import istest

from provy.more.debian import DjangoRole, AptitudeRole, PipRole, SupervisorRole
from provy.more.debian.web.django import SITES_KEY
from tests.unit.tools.helpers import ProvyTestCase


class DjangoRoleTest(ProvyTestCase):
    def setUp(self):
        super(DjangoRoleTest, self).setUp()
        self.role = DjangoRole(prov=None, context={'owner': 'some-owner'})
        self.supervisor_role = SupervisorRole(prov=None, context=self.role.context)

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude, self.mock_role_method('register_template_loader'), self.using_stub(PipRole) as pip:
            self.role.provision()

            self.role.register_template_loader.assert_called_with('provy.more.debian.web')
            aptitude.ensure_package_installed.assert_called_with('python-mysqldb')
            self.assertEqual(pip.ensure_package_installed.mock_calls, [
                call('django'),
                call('gunicorn'),
            ])

    @istest
    def installs_necessary_packages_to_provision_with_version(self):
        with self.using_stub(AptitudeRole) as aptitude, self.mock_role_method('register_template_loader'), self.using_stub(PipRole) as pip:
            self.role.context['django-version'] = '1.5.1'
            self.role.provision()

            self.role.register_template_loader.assert_called_with('provy.more.debian.web')
            aptitude.ensure_package_installed.assert_called_with('python-mysqldb')
            self.assertEqual(pip.ensure_package_installed.mock_calls, [
                call('django', version=self.role.context['django-version']),
                call('gunicorn'),
            ])

    @istest
    def requires_a_settings_path_to_create_site(self):

        def create_site():
            with self.role.create_site('some-site') as site:
                site.settings_path = None

        self.assertRaises(RuntimeError, create_site)

    @istest
    def prepares_site_under_supervisor(self):
        with self.using_stub(SupervisorRole), self.role.using(SupervisorRole) as supervisor_role:
            supervisor_role.log_folder = '/supervisor/log/folder'
            with self.role.create_site('some-site') as site:
                site.settings_path = '/some/settings.path'

        self.assertTrue(site.use_supervisor)
        self.assertEqual(site.supervisor_log_folder, supervisor_role.log_folder)
        self.assertFalse(site.daemon)
        self.assertFalse(site.auto_start)

    @istest
    def prepares_site_without_supervisor(self):
        with self.role.create_site('some-site') as site:
            site.settings_path = '/some/settings.path'

        self.assertFalse(site.use_supervisor)
        self.assertEqual(site.supervisor_log_folder, '/var/log')
        self.assertTrue(site.daemon)
        self.assertTrue(site.auto_start)

    @istest
    def guarantees_that_site_is_prepared_for_supervisor(self):
        with self.using_stub(SupervisorRole), self.role.using(SupervisorRole) as supervisor_role:
            supervisor_role.log_folder = '/supervisor/log/folder'
            with self.role.create_site('some-site') as site:
                site.settings_path = '/some/settings.path'

        self.assertIn(site, self.role.context[SITES_KEY])
        self.assertTrue(self.role.restart_supervisor_on_changes)

    @istest
    def guarantees_that_site_is_prepared_for_standalone(self):
        with self.role.create_site('some-site') as site:
            site.settings_path = '/some/settings.path'

        self.assertIn(site, self.role.context[SITES_KEY])
        self.assertFalse(self.role.restart_supervisor_on_changes)

    @istest
    def does_nothing_on_cleanup_if_nothing_done(self):
        '''This is just a dumb test to see if cleanup() doesn't break when there's nothing to cleanup.'''

        self.role.cleanup()

    @istest
    def installs_each_configured_site(self):
        with self.using_stub(SupervisorRole), self.role.using(SupervisorRole) as supervisor_role:
            supervisor_role.log_folder = '/supervisor/log/folder'

            with self.role.create_site('foo_site') as foo_site:
                foo_site.settings_path = '/some/settings.path'

            with self.role.create_site('bar_site') as bar_site:
                bar_site.settings_path = '/some/settings.path'

        with self.mock_role_methods('_update_init_script', '_update_settings', '_update_supervisor_program', '_restart'), self.using_stub(SupervisorRole) as supervisor_role:
            self.role._update_init_script.return_value = True
            self.role._update_settings.return_value = True

            self.role.cleanup()

            self.assertEqual(self.role._update_init_script.mock_calls, [call(foo_site), call(bar_site)])
            self.assertEqual(self.role._update_settings.mock_calls, [call(foo_site), call(bar_site)])
            self.assertEqual(self.role._update_supervisor_program.mock_calls, [call(foo_site), call(bar_site)])
            self.assertEqual(self.role._restart.mock_calls, [call(foo_site), call(bar_site)])

            supervisor_role.ensure_restart.assert_called_with()

    @istest
    def installs_each_configured_site_without_supervisor(self):
        with self.role.create_site('foo_site') as foo_site:
            foo_site.settings_path = '/some/settings.path'

        with self.mock_role_methods('_update_init_script', '_update_settings', '_update_supervisor_program', '_restart'), self.using_stub(SupervisorRole) as supervisor_role:
            self.role._update_init_script.return_value = True
            self.role._update_settings.return_value = True

            self.role.cleanup()

            self.role._restart.assert_called_once_with(foo_site)

            self.assertFalse(self.role._update_supervisor_program.called)
            self.assertFalse(supervisor_role.ensure_restart.called)

    @istest
    def doesnt_restart_on_cleanup_if_settings_not_updated(self):
        with self.role.create_site('foo_site') as foo_site:
            foo_site.settings_path = '/some/settings.path'

        with self.mock_role_methods('_update_init_script', '_update_settings', '_restart'):
            self.role._update_init_script.return_value = False
            self.role._update_settings.return_value = False

            self.role.cleanup()

            self.assertFalse(self.role._restart.called)

    @istest
    def updates_supervisor_program_with_site(self):
        website = self.role.create_site('foo-site')
        website.starting_port = 8000
        website.processes = 2
        website.settings_path = '/some/settings/path/settings.conf'
        website.user = 'some-user'
        website.supervisor_log_folder = '/some/log/folder'

        programs = [MagicMock(), MagicMock()]

        with self.using_stub(SupervisorRole) as supervisor_role:
            mock_with_program = supervisor_role.with_program.return_value
            mock_with_program.__enter__.side_effect = programs

            self.role._update_supervisor_program(website)

            self.assertEqual(programs[0].directory, '/some/settings/path')
            self.assertEqual(programs[0].command, '/etc/init.d/foo-site-8000 start')
            self.assertEqual(programs[0].name, 'foo-site-8000')
            self.assertEqual(programs[0].number_of_processes, 1)
            self.assertEqual(programs[0].user, website.user)
            self.assertEqual(programs[0].log_folder, website.supervisor_log_folder)

            self.assertEqual(programs[1].directory, '/some/settings/path')
            self.assertEqual(programs[1].command, '/etc/init.d/foo-site-8001 start')
            self.assertEqual(programs[1].name, 'foo-site-8001')
            self.assertEqual(programs[1].number_of_processes, 1)
            self.assertEqual(programs[1].user, website.user)
            self.assertEqual(programs[1].log_folder, website.supervisor_log_folder)

    @istest
    def restarts_site_when_running(self):
        website = self.role.create_site('bar-site')
        website.pid_file_path = '/foo/'

        with self.mock_role_methods('execute', 'remote_exists'):
            self.role.remote_exists.return_value = True

            self.role._restart(website)

            self.assertEqual(self.role.remote_exists.mock_calls, [
                call('/foo/bar-site_8000.pid'),
            ])
            self.assertEqual(self.role.execute.mock_calls, [
                call('/etc/init.d/bar-site-8000 stop', stdout=False, sudo=True),
                call('/etc/init.d/bar-site-8000 start', stdout=False, sudo=True),
            ])

    @istest
    def restarts_site_when_not_running(self):
        website = self.role.create_site('bar-site')
        website.pid_file_path = '/foo/'

        with self.mock_role_methods('execute', 'remote_exists'):
            self.role.remote_exists.return_value = False

            self.role._restart(website)

            self.assertEqual(self.role.remote_exists.mock_calls, [
                call('/foo/bar-site_8000.pid'),
            ])
            self.assertEqual(self.role.execute.mock_calls, [
                call('/etc/init.d/bar-site-8000 start', stdout=False, sudo=True),
            ])

    @istest
    def doesnt_restart_when_not_autostarting(self):
        website = self.role.create_site('bar-site')
        website.auto_start = False

        with self.mock_role_methods('execute', 'remote_exists'):
            self.role._restart(website)

            self.assertFalse(self.role.remote_exists.called)
            self.assertFalse(self.role.execute.called)

    @istest
    def updates_settings(self):
        with self.role.create_site('bar-site') as website:
            website.settings_path = '/foo/settings.py'

        with self.mock_role_method('update_file'):
            self.role.update_file.return_value = 'some result'

            result = self.role._update_settings(website)

            self.assertEqual(result, 'some result')
            self.role.update_file.assert_called_once_with('local.settings.template', '/foo/local_settings.py', owner=None, sudo=True, options={'settings': {}, 'settings_file': 'settings'})
