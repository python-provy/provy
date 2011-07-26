#!/usr/bin/env python

from pyvows import Vows, expect

from provy.more.debian import PipRole

class PipMockedRole(PipRole):

    def __init__(self, *args, **kwargs):
        super(PipMockedRole, self).__init__(*args, **kwargs)
        self.should_be_mocked = {}

    def __getattribute__(self, attr_name):
        attribute = PipRole.__getattribute__(self, attr_name)
        if "mock_method" != attr_name and \
            hasattr(attribute, '__call__') and \
                attr_name in self.should_be_mocked:
            return self.should_be_mocked[attr_name]
        else:
            return attribute

    def mock_method(self, method_name, return_value):
        class Mock(object):
            def __init__(self):
                self.calls = []

            def __call__(self, *args, **kwargs):
                self.calls.append({"args": args, "kwargs": kwargs })
                return return_value

        self.should_be_mocked[method_name] = Mock()

@Vows.assertion
def to_be_called(function):
    assert len(function.calls) > 0

@Vows.assertion
def to_be_called_with(function, *args, **kwargs):
    be_called = False
    for call in function.calls:
        if call['args'] == args and call['kwargs'] == kwargs:
            be_called = True
    assert be_called, "The function should be called with %s, %s, but not was" % (str(args), str(kwargs))

@Vows.assertion
def to_be_called_like(function, *args):
    be_called = False
    for call in function.calls:
        if call['args'] == args:
            be_called = True
    assert be_called

@Vows.assertion
def not_to_be_called(function):
    assert len(function.calls) == 0

@Vows.batch
class TestPipRole(Vows.Context):

    class TestEnsurePackageInstalled(Vows.Context):
        def topic(self):
            pip_role = PipMockedRole(prov=None, context={})
            pip_role.mock_method("log", None)
            pip_role.mock_method("execute", None)
            return pip_role

        class WhenPackageIsInstalled(Vows.Context):
            def topic(self, pip_role):
                pip_role.mock_method("is_package_installed", True)
                pip_role.ensure_package_installed("django")
                return pip_role

            def should_ask_if_package_are_installed(self, topic):
                expect(topic.is_package_installed).to_be_called_with("django")

            def should_be_executed_none_commands(self, topic):
                expect(topic.execute).not_to_be_called()

            class WhenASpecifcVersionOfPackageIsInstalled(Vows.Context):
                def topic(self, pip_role):
                    pip_role.mock_method("is_package_installed", True)
                    pip_role.ensure_package_installed("django", version="1.2.3")
                    return pip_role

                def should_ask_if_package_are_installed(self, topic):
                    expect(topic.is_package_installed).to_be_called_with("django", "1.2.3")

                def should_be_executed_none_commands(self, topic):
                    expect(topic.execute).not_to_be_called()

                class WhenPackageIsNotInstalled(Vows.Context):
                    def topic(self, pip_role):
                        pip_role.mock_method("is_package_installed", False)
                        pip_role.ensure_package_installed("django")
                        return pip_role

                    def should_ask_if_package_are_installed(self, topic):
                        expect(topic.is_package_installed).to_be_called_with("django")

                    def should_execute_the_package_install(self, topic):
                        expect(topic.execute).to_be_called_like("pip install django")

                    class WhenIWantToInstallASpecificVersionOfThePackage(Vows.Context):
                        def topic(self, pip_role):
                            pip_role.mock_method("is_package_installed", False)
                            pip_role.ensure_package_installed("django", version="1.2.3")
                            return pip_role

                        def should_ask_if_package_are_installed(self, topic):
                            expect(topic.is_package_installed).to_be_called_with("django", "1.2.3")

                        def should_execute_the_package_install(self, topic):
                            expect(topic.execute).to_be_called_like("pip install django==1.2.3")

                        class WhenIWantToGetALowerVersionOfThePackage(Vows.Context):
                            def topic(self, pip_role):
                                pip_role.mock_method("is_package_installed", False)
                                pip_role.ensure_package_installed("django", version=">=1.2.3")
                                return pip_role

                            def should_ask_if_package_are_installed(self, topic):
                                expect(topic.is_package_installed).to_be_called_with("django", "1.2.3")

                            def should_execute_the_package_install(self, topic):
                                expect(topic.execute).to_be_called_like("pip install django>=1.2.3")

