Contributing
============

Contributions are very welcome. Specially roles. If you implement a role that you think others might be using, please contribute.

To contribute head to `provy's github page <https://github.com/python-provy/provy>`_, fork it and create a pull request.

Developing
----------

Make it great :-)
*****************

We strive to keep the internal quality of provy to the best that we can;
Therefore, it's very important to keep some things in mind when contributing with code for provy:

* Test everything you can, with automated tests. If possible, please develop code with `TDD <http://en.wikipedia.org/wiki/Test-driven_development>`_.
  If you're having a hard time building tests, don't hesitate to ask for help in the `provy mailing list <http://groups.google.com/group/provy>`_.
  We are happy to help you keep your code well-covered by tests;

* When writing actual code, follow the conventions in `PEP 8 <http://www.python.org/dev/peps/pep-0008/>`_
  (except for `maximum line length <http://www.python.org/dev/peps/pep-0008/#maximum-line-length>`_,
  which we don't follow because there are too many parts of the project that require large strings to be used);

* When writing docstrings, follow the conventions in `PEP 257 <http://www.python.org/dev/peps/pep-0257/>`_
  (take a look at other docstrings in the project to get a feel of how we organize them);

  - Also, when writing docstrings for the API, provide examples of how that method or class works.
    Having a code example of a part of the API is really helpful for the user.

Setting up your environment
***************************

1. Make sure `pip <http://www.pip-installer.org/>`_, `virtualenv <http://www.virtualenv.org/>`_ and `virtualenvwrapper <http://virtualenvwrapper.readthedocs.org/>`_ are installed;
2. Create a virtual environment for provy:

  .. code-block:: sh

      $ mkvirtualenv provy

3. Install the requirements:

  .. code-block:: sh

      $ pip install -r REQUIREMENTS

4. Run your first provy build, to make sure everything's ready for you to start developing:

  .. code-block:: sh

      $ make build

  The command should run without accusing any error.

How to develop
**************

There are basically two commands we run, when developing.

When building code, you need to test it and check if the code format is OK with the conventions we use:

.. code-block:: sh

    $ make build

This Makefile target essentially does these steps:

1. It runs the tests over the project;
2. It builds a code coverage report (you should take a look if the total code coverage is not decreasing, when you build your code);
3. It runs `flake8 <http://pypi.python.org/pypi/flake8/>`_ over the entire codebase, making sure the code style is following the conventions mentioned above.

It's also important to keep the codebase well documented. We use Sphinx to generate the documentation,
which is also used when our docs go to `Read The Docs <https://provy.readthedocs.org>`_.

To build the docs in your environment, in order to test it locally (this is very useful to see how your docs will look like when they are rolled out),
first go to the `provy/docs` directory, then run:

.. code-block:: sh

    $ make html

Some warnings may show up in the command output - you should listen to them, in order to spot possible documentation problems -.

The team
--------

The core team
*************

The core team behind provy (in order of joining the project):

* `Bernardo Heynemann <http://about.me/heynemann>`_ (technical leader of this project)
* `Rafael Carício <http://about.me/rafaelcaricio>`_
* `Douglas Andrade <https://github.com/dsarch>`_
* `Thiago Avelino <http://avelino.us/>`_
* `Diogo Baeder <http://diogobaeder.com.br/>`_

Other contributors
******************

Other non-core members, but equally important, equally rocking, equally ass-kicking contributors can be seen in this list:
https://github.com/python-provy/provy/network/members

There are also some more contributors that haven't send code to the project, but who help in other ways, when and how they can.
We're very happy to have you, guys! :-)