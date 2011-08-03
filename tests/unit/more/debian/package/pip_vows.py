#!/usr/bin/env python

from pyvows import Vows, expect

from provy.core.roles import Role
from provy.more.debian import PipRole

from unit.tools.role_context import RoleContext
from unit.tools.extra_assertions import *

@Vows.batch
class TestPipRole(RoleContext):

    def _role_class(self):
        return PipRole

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

                        class WhenIWantToGetALowerVersionOfThePackage(RoleContext):
                            def topic(self, pip_role):
                                pip_role.mock_method("is_package_installed", False)
                                pip_role.ensure_package_installed("django", version=">=1.2.3")
                                return pip_role

                            def should_ask_if_package_are_installed(self, topic):
                                expect(topic.is_package_installed).to_have_been_called_with("django", "1.2.3")

                            def should_execute_the_package_install(self, topic):
                                expect(topic.execute).to_have_been_called_like("pip install django>=1.2.3")

