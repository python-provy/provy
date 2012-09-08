#!/usr/bin/env python

from pyvows import Vows, expect

#from provy.more.debian import PipRole
from provy.more.debian.database.postgresql import PostgreSQLRole

from unit.tools.role_context import RoleContext
from unit.tools.extra_assertions import *


@Vows.batch
class TestPostgresRole(RoleContext):

    def _role_class(self):
        return PostgreSQLRole

    class TestIsUserCreated(RoleContext):
        def topic(self):
            role = self._get_role()
            return role

        class WhenUsernameIsProvidedAndPasswordIsAsked(RoleContext):
            def topic(self, role):
                self.role = role
                role.mock_method("execute", True)
                return self.role.create_user("foo")

            def should_create_a_user_with_password_prompt_via_createuser_command(self, topic):
                expect(self.role.execute).to_have_been_called_with("createuser -P foo", stdout=False)

            def should_have_created_the_user(self, topic):
                expect(topic).to_be_true()
