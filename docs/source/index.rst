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

What's provy and provisioning
=============================

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

Installing provy
================
Before installing provy you will need to ensure you have swig installed, as m2crypto needs it. Here is how to install it in some platforms.

Install the OS dependencies
---------------------------

MacOSX
++++++
To install swig on a mac, the easiest way is to install using the `homebrew package manager <http://mxcl.github.com/homebrew/>`_ (which we will not cover here). After installing it, execute this command::

    brew install https://raw.github.com/cobrateam/formulae/master/swig.rb

Ubuntu and Debian GNU/Linux
+++++++++++++++++++++++++++
It is just an apt-get install away =) ::

    $ sudo apt-get install swig

Arch Linux
++++++++++
Swig is in the extra repository and can be installed with::

    $ sudo pacman -S swig

Other platforms
+++++++++++++++
If your platform is not listed above, try searching in your package manager for *swig* and install it given the search results.

Install provy
-------------
Now that you have *swig*, installing *provy* is as easy as::

    $ pip install provy

It can be easily installed from source as well, like this::

    $ # make sure fabric, jinja2 and m2crypto are installed
    $ pip install fabric
    $ pip install jinja2
    $ pip install m2crypto
 
    $ # now actually installing it
    $ git clone git@github.com:heynemann/provy.git
    $ python setup.py install
    $ provy --version

As can be seen above, after being installed a *provy* command becomes available.

provy is `FOSS <http://en.wikipedia.org/wiki/Free_and_open_source_software>`_ and you can find its source code at `its github page <https://github.com/heynemann/provy>`_.

Getting started
===============



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

