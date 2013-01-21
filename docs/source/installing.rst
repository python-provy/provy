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