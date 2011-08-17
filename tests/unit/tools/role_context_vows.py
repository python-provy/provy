#!/usr/bin/env python

from pyvows import Vows, expect

from provy.core.roles import Role

from unit.tools.role_context import RoleContext, MockedRole
from unit.tools.extra_assertions import *

class FakeRole(Role):

    def other(self, o):
        pass

    def original_method(self, param):
        self.other(param)
        return "yeah!"

    def yes_another(self, to_return):
        return to_return

@Vows.batch
class TestWhenINotImplementTheGetRoleMethod(RoleContext):

    def topic(self):
        return self._get_role()

    def should_be_raised_an_error(self, topic):
        expect(topic).to_be(NotImplementedError)

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


