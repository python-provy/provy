What are roles?
===============

Roles are the most important concept in *provy*. A role specifies one server capability, like user management or a package provider.

*provy* comes with many bundled roles, but you can very easily create your own roles. As a matter of fact, if you followed the :doc:`getting-started` tutorial, you have already created two custom roles.

Creating new roles is as easy as creating a class that inherits from *provy.Role* and implements a *provision* method.

This method is the one *provy* will call when this role is being provisioned into a given server.