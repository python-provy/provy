Custom Files and Templating
===========================

Some methods provided by provy (including *update_file*) support passing in options that may be used in templates.

*provy* uses `jinja2 <http://jinja.pocoo.org/>`_ for templating, thus supporting if/else statements, loops and much more. It's advised that you take a look at `jinja2 <http://jinja.pocoo.org/>`_ docs.

`jinja2 <http://jinja.pocoo.org/>`_ will look for files in two different places. The first one and probably the one you'll use the most, is a directory called *files* in the same path as *provyfile.py*.

Any files you place inside this directory may be used as templates to be uploaded to the server being provisioned. Since *provy* is built on top of `fabric <http://fabfile.org/>`_, you can use its *put* method as well to put any file or folder to the server. It's advised to use the bundled methods that come with provy, though, as those are `idempotent <http://en.wikipedia.org/wiki/Idempotence>`_.

The other place you can put files is in a *templates* directory inside Role apps. The supervisor role uses this approach, if you want to take a look at an example. If you do place files in the *templates* directory, do not forget to call the *register_template_loader* method passing in the full namespace of your app (more details in the provy.more section below).

We used custom files in the `Getting started`_ section to provide the needed configuration files for `nginx <http://www.nginx.org/>`_.