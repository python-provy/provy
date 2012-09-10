#!/usr/bin/env python

from os.path import join, abspath, dirname
from pyvows import Vows, expect

from provy.more.debian import PipRole

from unit.tools.role_context import RoleContext
from unit.tools.extra_assertions import *


@Vows.batch
class TestPipRole(RoleContext):

    def _role_class(self):
        return PipRole

    class WhenIWantToSplitPackageInput(RoleContext):
        def topic(self):
            role = self._get_role()
            return role

        class WhenIUseASimpleName(RoleContext):
            def topic(self, role):
                return role.extract_package_data_from_input("django")

            def should_return_the_package_name(self, topic):
                expect(topic).to_be_like({"name": "django"})

        class WhenISpecifyThePackageVersion(RoleContext):
            def topic(self, role):
                return role.extract_package_data_from_input("django==1.2.3")

            def should_return_the_package_name_and_version(self, topic):
                expect(topic).to_be_like({"name": "django", "version": "1.2.3", "version_constraint": "=="})

        class WhenISpecifyThePackageVersionGreatherThan(RoleContext):
            def topic(self, role):
                return role.extract_package_data_from_input("django>=1.2.3")

            def should_return_the_package_name_and_version(self, topic):
                expect(topic).to_be_like({"name": "django", "version": "1.2.3", "version_constraint": ">="})

        class WhenISpecifyTheRepositoryPath(RoleContext):
            def topic(self, role):
                return role.extract_package_data_from_input("-e hg+http://bitbucket.org/bkroeze/django-keyedcache/#egg=django-keyedcache")

            def should_return_the_package_name(self, topic):
                expect(topic).to_be_like({"name": "django-keyedcache"})

        class WhenISpecifyThePackageFileUrl(RoleContext):
            def topic(self, role):
                return role.extract_package_data_from_input("http://www.satchmoproject.com/snapshots/trml2pdf-1.2.tar.gz")

            def should_return_the_package_url_as_packeage_name(self, topic):
                expect(topic).to_be_like({"name": "http://www.satchmoproject.com/snapshots/trml2pdf-1.2.tar.gz"})

    class TestIsPackageInstalled(RoleContext):
        def topic(self):
            role = self._get_role()
            role.mock_method("execute", "django==1.2.3")
            return role

        class WhenUsedOnlyPackageName(RoleContext):
            def topic(self, role):
                role.is_package_installed("django")
                return role

            def should_execute_the_correct_command(self, role):
                expect(role.execute).to_have_been_called_like("pip freeze | tr '[A-Z]' '[a-z]' | grep django")

            class WhenUsedPackageNameAndVersion(RoleContext):
                def topic(self, role):
                    self.role = role
                    return role.is_package_installed("django==1.2.3")

                def should_execute_the_correct_command(self, topic):
                    expect(self.role.execute).to_have_been_called_like("pip freeze | tr '[A-Z]' '[a-z]' | grep django")

                def the_packeage_should_be_installed(self, topic):
                    expect(topic).to_be_true()

            class WhenIHaveInstalledTheLowerVersion(RoleContext):
                def topic(self, role):
                    return role.is_package_installed("django>=1.3.0")

                def the_package_should_not_be_installed(self, topic):
                    expect(topic).to_be_false()

            class WhenIHaveInstalledTheLowerVersionAndPassVersionViaParam(RoleContext):
                def topic(self, role):
                    return role.is_package_installed("django", "1.3.0")

                def the_package_should_not_be_installed(self, topic):
                    expect(topic).to_be_false()

            class WhenIDontHavePackageInstalled(RoleContext):
                def topic(self):
                    role = self._get_role()
                    role.mock_method("execute", "")
                    return role.is_package_installed("django", "1.3.0")

                def the_package_should_not_be_installed(self, topic):
                    expect(topic).to_be_false()

    class WhenIWantToInstallFromARequerimentsFile(RoleContext):
        def topic(self):
            role = self._get_role()
            role.mock_method("ensure_package_installed", None)
            role.ensure_requeriments_installed(abspath(join(dirname(__file__), "../../../fixtures/for_testing.txt")))
            return role

        def should_ensure_django_installed(self, role):
            expect(role.ensure_package_installed).to_have_been_called_with("Django")

        def should_ensure_yolk_installed(self, role):
            expect(role.ensure_package_installed).to_have_been_called_with("yolk==0.4.1")

        def should_ensure_specific_file_installed(self, role):
            expect(role.ensure_package_installed).to_have_been_called_with("http://www.satchmoproject.com/snapshots/trml2pdf-1.2.tar.gz")

        def should_ensure_from_repository_installed(self, role):
            expect(role.ensure_package_installed).to_have_been_called_with("-e hg+http://bitbucket.org/bkroeze/django-threaded-multihost/#egg=django-threaded-multihost")

    class TestEnsurePackageInstalled(RoleContext):
        def topic(self):
            pip_role = self._get_role()
            pip_role.mock_method("log", None)
            pip_role.mock_method("execute", None)
            return pip_role

        class WhenPackageIsInstalled(RoleContext):
            def topic(self, pip_role):
                pip_role.mock_method("is_package_installed", True)
                pip_role.ensure_package_installed("django")
                return pip_role

            def should_ask_if_package_are_installed(self, topic):
                expect(topic.is_package_installed).to_have_been_called_with("django")

            def should_be_executed_none_commands(self, topic):
                expect(topic.execute).not_to_have_been_called()

            class WhenASpecifcVersionOfPackageIsInstalled(RoleContext):
                def topic(self, pip_role):
                    pip_role.mock_method("is_package_installed", True)
                    pip_role.ensure_package_installed("django", version="1.2.3")
                    return pip_role

                def should_ask_if_package_are_installed(self, topic):
                    expect(topic.is_package_installed).to_have_been_called_with("django", "1.2.3")

                def should_be_executed_none_commands(self, topic):
                    expect(topic.execute).not_to_have_been_called()

                class WhenPackageIsNotInstalled(RoleContext):
                    def topic(self, pip_role):
                        pip_role.mock_method("is_package_installed", False)
                        pip_role.ensure_package_installed("django")
                        return pip_role

                    def should_ask_if_package_are_installed(self, topic):
                        expect(topic.is_package_installed).to_have_been_called_with("django")

                    def should_execute_the_package_install(self, topic):
                        expect(topic.execute).to_have_been_called_like("pip install django")

                    class WhenIWantToInstallASpecificVersionOfThePackage(RoleContext):
                        def topic(self, pip_role):
                            pip_role.mock_method("is_package_installed", False)
                            pip_role.ensure_package_installed("django", version="1.2.3")
                            return pip_role

                        def should_ask_if_package_are_installed(self, topic):
                            expect(topic.is_package_installed).to_have_been_called_with("django", "1.2.3")

                        def should_execute_the_package_install(self, topic):
                            expect(topic.execute).to_have_been_called_like("pip install django==1.2.3")

                        class WhenIWantToGetAGreatherVersionOfThePackage(RoleContext):
                            def topic(self, pip_role):
                                pip_role.mock_method("is_package_installed", False)
                                pip_role.ensure_package_installed("django", version=">=1.2.3")
                                return pip_role

                            def should_ask_if_package_are_installed(self, topic):
                                expect(topic.is_package_installed).to_have_been_called_with("django", "1.2.3")

                            def should_execute_the_package_install(self, topic):
                                expect(topic.execute).to_have_been_called_like("pip install django>=1.2.3")

