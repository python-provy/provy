#!/usr/bin/env python

from pyvows import Vows, expect

from provy.core.roles import Role
from provy.more.debian import PipRole

class MockedRole(object):

    class Mock(object):
        def __init__(self, return_value):
            self.return_value = return_value
            self.calls = []

        def __call__(self, *args, **kwargs):
            self.calls.append({"args": args, "kwargs": kwargs })
            return self.return_value

    def __init__(self, role_class):
        self.should_be_mocked = {}
        self.role = role_class(prov=None, context={})

    def __getattr__(self, attr_name):
        if attr_name in self.should_be_mocked:
            return self.should_be_mocked[attr_name]

        class Wrapper(self.role.__class__):
            def __getattribute__(s, an):
                return self.__getattr__(an)

        def wrapper(*args, **kwargs):
            return getattr(self.role.__class__, attr_name)(Wrapper(None, {}), *args, **kwargs)
        return wrapper

    def mock_method(self, method_name, return_value):
        self.should_be_mocked[method_name] = MockedRole.Mock(return_value)

class RoleContext(Vows.Context):

    def _get_role(self):
        if hasattr(self, 'parent') and self.parent:
            return self.parent._get_role()
        else:
            return MockedRole(self._role_class())

    def _role_class(self):
        raise NotImplementedError

@Vows.assertion
def to_have_been_called(function):
    assert len(function.calls) > 0

@Vows.assertion
def to_have_been_called_with(function, *args, **kwargs):
    be_called = False
    for call in function.calls:
        if call['args'] == args and call['kwargs'] == kwargs:
            be_called = True
    assert be_called, "The function should be called with %s, %s, but not was" % (str(args), str(kwargs))

@Vows.assertion
def to_have_been_called_like(function, *args):
    be_called = False
    for call in function.calls:
        if call['args'] == args:
            be_called = True
    assert be_called

@Vows.assertion
def not_to_have_been_called(function):
    assert len(function.calls) == 0

@Vows.assertion
def to_have_attr(obj, attr_name):
    assert hasattr(obj, attr_name)

@Vows.assertion
def to_be(obj, type_class):
    assert type(obj) == type_class or isinstance(obj, type_class) or obj == type_class

@Vows.assertion
def not_to_be(obj, type_class):
    assert type(obj) != type_class and not isinstance(obj, type_class) and obj != type_class

@Vows.assertion
def to_have_key(dict_obj, key):
    assert key in dict_obj

class FakeRole(Role):

    def other(self, o):
        pass

    def original_method(self, param):
        self.other(param)
        return "yeah!"

    def yes_another(self, to_return):
        return to_return

@Vows.batch
class TestMockRole(RoleContext):

    def _role_class(self):
        return FakeRole

    def topic(self):
        return self._get_role()

    def ensure_mock_method_exists(self, topic):
        expect(topic).to_have_attr('mock_method')

    def ensure_mock_method_can_be_called(self, topic):
        expect(topic.mock_method).to_have_attr('__call__')

    def ensure_attribute_should_be_mocked_available(self, topic):
        expect(topic).to_have_attr('should_be_mocked')

    def ensure_attribute_should_be_mocked_to_be_a_dict(self, topic):
        expect(topic.should_be_mocked).to_be(dict)

    class WhenICallTheMockMethod(RoleContext):

        def topic(self, role):
            role.mock_method('other', 'fine')
            return role

        def ensure_method_included_in_mocked_dict(self, role):
            expect(role.should_be_mocked).to_have_key('other')

        def ensure_method_has_been_mocked(self, role):
            expect(role.other).to_be(MockedRole.Mock)

        class WhenICallTheMockedMethod(RoleContext):

            def topic(self):
                role = self._get_role()
                role.mock_method('other', 'fine')
                return [role, role.other('hello')]

            def ensure_method_attached_in_role_returns_the_mocked_value(self, topic):
                expect(topic[1]).to_equal('fine')

            def should_store_the_call(self, topic):
                expect(topic[0].other).to_have_been_called()

        class TheMockedMethodShouldHaveTheOriginalMethods(RoleContext):

            def should_have_the_original_method(self, role):
                expect(role).to_have_attr('original_method')

            def should_return_the_original_method(self, role):
                expect(role.original_method).not_to_be(MockedRole.Mock)

            class WhenICallTheOriginalMethodThatsCallTheMockedMethodInternally(RoleContext):

                def topic(self, role):
                    return [role, role.original_method("hello")]

                def should_call_the_mocked_method(self, topic):
                    expect(topic[0].other).to_have_been_called()

                def should_execute_normally_the_original_method(self, topic):
                    expect(topic[1]).to_equal("yeah!")

            class WhenICallAnotherMethod(RoleContext):

                def topic(self, role):
                    return role.yes_another("be nice!")

                def should_execute_without_modification(self, topic):
                    expect(topic).to_equal("be nice!")


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

        class WhenPackageIsInstalled(Vows.Context):
            def topic(self, pip_role):
                pip_role.mock_method("is_package_installed", True)
                pip_role.ensure_package_installed("django")
                return pip_role

            def should_ask_if_package_are_installed(self, topic):
                expect(topic.is_package_installed).to_have_been_called_with("django")

            def should_be_executed_none_commands(self, topic):
                expect(topic.execute).not_to_have_been_called()

            class WhenASpecifcVersionOfPackageIsInstalled(Vows.Context):
                def topic(self, pip_role):
                    pip_role.mock_method("is_package_installed", True)
                    pip_role.ensure_package_installed("django", version="1.2.3")
                    return pip_role

                def should_ask_if_package_are_installed(self, topic):
                    expect(topic.is_package_installed).to_have_been_called_with("django", "1.2.3")

                def should_be_executed_none_commands(self, topic):
                    expect(topic.execute).not_to_have_been_called()

                class WhenPackageIsNotInstalled(Vows.Context):
                    def topic(self, pip_role):
                        pip_role.mock_method("is_package_installed", False)
                        pip_role.ensure_package_installed("django")
                        return pip_role

                    def should_ask_if_package_are_installed(self, topic):
                        expect(topic.is_package_installed).to_have_been_called_with("django")

                    def should_execute_the_package_install(self, topic):
                        expect(topic.execute).to_have_been_called_like("pip install django")

                    class WhenIWantToInstallASpecificVersionOfThePackage(Vows.Context):
                        def topic(self, pip_role):
                            pip_role.mock_method("is_package_installed", False)
                            pip_role.ensure_package_installed("django", version="1.2.3")
                            return pip_role

                        def should_ask_if_package_are_installed(self, topic):
                            expect(topic.is_package_installed).to_have_been_called_with("django", "1.2.3")

                        def should_execute_the_package_install(self, topic):
                            expect(topic.execute).to_have_been_called_like("pip install django==1.2.3")

                        class WhenIWantToGetALowerVersionOfThePackage(Vows.Context):
                            def topic(self, pip_role):
                                pip_role.mock_method("is_package_installed", False)
                                pip_role.ensure_package_installed("django", version=">=1.2.3")
                                return pip_role

                            def should_ask_if_package_are_installed(self, topic):
                                expect(topic.is_package_installed).to_have_been_called_with("django", "1.2.3")

                            def should_execute_the_package_install(self, topic):
                                expect(topic.execute).to_have_been_called_like("pip install django>=1.2.3")

