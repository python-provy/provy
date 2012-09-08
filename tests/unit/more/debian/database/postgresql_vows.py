#!/usr/bin/env python

from pyvows import Vows, expect

#from provy.more.debian import PipRole
from provy.more.debian.database.postgresql import PostgresqlRole

from unit.tools.role_context import RoleContext
from unit.tools.extra_assertions import *


@Vows.batch
class TestPostgresRole(RoleContext):

    def _role_class(self):
        return PostgresqlRole

    class TestIsUserCreated(RoleContext):
        def topic(self):
            role = self._get_role()
            return role.mock_method("execute")

        class WhenUsernameIsProvidedAndPasswordIsAsked(RoleContext):
            def topic(self, role):
                self.role = role
                return self.role.create_user("foo")

            def should_create_a_user_with_password_prompt(self, topic):
                expect(self.role.execute).to_have_been_called_like("createuser -P foo", stdout=False)
