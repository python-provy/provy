.. provy documentation master file, created by
   sphinx-quickstart on Sun Jan 20 04:54:01 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=====
provy
=====
**Python** provisioning made **easy**!

About
=====

**provy** is an easy-to-use provisioning system in python.

Turn that tedious task of provisioning the infrastructure of your website into a repeatable no-frills reliable process.

Getting started
===============

What's provy and provisioning
-----------------------------

According to `Wikipedia <http://en.wikipedia.org/wiki/Provisioning>`_, provisioning is "the process of preparing and equipping a network to allow it to provide (new) services to its users".

We'll draw from this concept the part of preparing and equipping.

**provy** is a infrastructure provisioning automation tool. Its main goal is making it easy to create highly-scalable architectures with simple scripts.

**provy** stands on the shoulder of giants! `fabric <http://docs.fabfile.org/>`_ for the networking part and `jinja2 <http://jinja.pocoo.org/>`_ for templating capabilities.

A very simple, yet working example of a valid provyfile.py::

    #!/usr/bin/python
    # -*- coding: utf-8 -*-

    from provy.core import Role
    from provy.more.debian import UserRole, AptitudeRole
 
    class SimpleServer(Role):
        def provision(self):
            with self.using(UserRole) as role:
                role.ensure_user('my-user', identified_by='my-pass', is_admin=True)
 
            with self.using(AptitudeRole) as role:
                role.ensure_package_installed('vim')
 
    servers = {
        'frontend': {
            'address': '33.33.33.33',
            'user': 'root',
            'roles': [
                SimpleServer
            ]
        }
    }



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

