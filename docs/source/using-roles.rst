Using Roles in my Roles
=======================

As you may have noticed, *provy* provides a special syntax for using other roles in your role. Say we need to use the *AptitudeRole* in our role. This is how we'd do it::

    class MyRole(Role):
        def provision(self):
            with self.using(AptitudeRole) as role:
                # do something with role
                role.ensure_package_installed('some-package')

The *using* method of the Role class is a special way of using other roles. The reason for using it is that it maintains context and the *provy* lifecycle (more on both later).

If you just want to provision another role in your role, you can use::

    class MyRole(Role):
        def provision(self):
            self.provision_role(TornadoRole)

The *provision_role* method does exactly the same as the *using* method, except it does not enter a with block. This should be used when you don't want to call anything in the role, instead just have it provisioned.