#!/usr/bin/env python

from pyvows import Vows, expect

from provy.core.roles import Role

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
        if getattr(self, 'parent'):
            return self.parent._get_role()
        else:
            return MockedRole(self._role_class())

    def _role_class(self):
        raise NotImplementedError


