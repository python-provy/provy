#!/usr/bin/env python

from pyvows import Vows, expect

#from provy.more.debian import PipRole
from provy.more.debian.database.postgresql import PostgreSQLRole

from unit.tools.role_context import RoleContext
from unit.tools.extra_assertions import *


@Vows.batch
class TestPostgresqlRoleUserCreation(RoleContext):

    def _role_class(self):
        return PostgreSQLRole

    class WhenUsernameIsProvidedAndPasswordIsAsked(RoleContext):
        def topic(self):
            self.role = self._get_role()
            self.role.mock_method("execute", True)
            return self.role.create_user("foo", ask_password=True)

        def should_create_a_user_with_password_prompt_via_createuser_command(self, topic):
            expect(self.role.execute).to_have_been_called_with("createuser -P foo", stdout=False)

        def should_have_created_the_user(self, topic):
            expect(topic).to_be_true()

    class WhenUsernameIsProvidedButPasswordPromptIsBypassed(RoleContext):
        def topic(self):
            self.role = self._get_role()
            self.role.mock_method("execute", True)
            return self.role.create_user("foo", ask_password=False)

        def should_create_a_user_without_password(self, topic):
            expect(self.role.execute).to_have_been_called_with("createuser foo", stdout=False)

        def should_have_created_the_user(self, topic):
            expect(topic).to_be_true()


@Vows.batch
class TestPostgresqlRoleUserRemoval(RoleContext):

    def _role_class(self):
        return PostgreSQLRole

    class WhenUserIsDropped(RoleContext):
        def topic(self):
            self.role = self._get_role()
            self.role.mock_method("execute", True)
            return self.role.drop_user("foo")

        def should_drop_the_user_by_the_name(self, topic):
            expect(self.role.execute).to_have_been_called_with("dropuser foo", stdout=False)

        def should_have_dropped_the_user(self, topic):
            expect(topic).to_be_true()
