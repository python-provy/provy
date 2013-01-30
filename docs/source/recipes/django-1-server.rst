Django + Nginx same server
==========================

In this recipe we'll be running a django website with 4 processes and 2 threads per process.

`Django <https://www.djangoproject.com/>`_, `gunicorn <http://gunicorn.org/>`_, `supervisor <http://supervisord.org/>`_ or `nginx <http://nginx.org/>`_
concepts and usage are beyond the scope of this recipe.

Our web server will be nginx and it will be responsible for `load balancing <http://en.wikipedia.org/wiki/Load_balancing_%28computing%29>`_ among our django
processes and for serving static files.

The load balancing will be made using `reverse proxying <http://en.wikipedia.org/wiki/Reverse_proxy>`_ to the 4 gunicorn processes, that are bound to ports 8000-8003.

The gunicorn processes will be monitored by supervisor. This is crucial to make sure that any process that fails is restarted.

All logs are recorded in the user's home "logs" directory.

Our user for this recipe is called `djangotutorial`.

The application
---------------

The application that we'll deploy is the app developed by following the `Django documentation tutorial <https://docs.djangoproject.com/en/1.3/intro/tutorial01/>`_.

There's a public repo at https://github.com/heynemann/django-tutorial. This is the repository we'll use to deploy our application.

It is a very simple application, but it serves us right in that it features django admin, static files and database access.

Pre-requisites
--------------

The obvious pre-requisites for our recipe is `provy`. For more instructions on how to install it, check the :doc:`Installing provy </installing>` section in `provy`'s main docs.

In this recipe we'll be using vagrant for our `local` server and amazon ec2 for our `production` server.

Using vagrant is completely optional, though. If you have a local server that you provision and deploy to, feel free to replace the address and user in `provyfile` with your own data.

You'll also need an account with `Amazon AWS <http://aws.amazon.com/>`_. Learning how to use Amazon EC2 is out of the scope of this recipe.
If you don't have a production server and you don't expect your website to have a very big hit, Amazon has a very generous `free tier <http://aws.amazon.com/free/>`_.

For the purposes of this recipe, consider we have a production server running at Amazon AWS (even if at the time you are reading this the server is not online).

The deployment process
----------------------

Our deployment script (fabric) will do the following steps:

a. Update git's clone in the server;
b. Run syncdb against the app repo in the server;
c. Run collectstatic against the app repo in the server;
d. Restart supervisor after everything.

This should be enough to have our app up-to-date in the webserver.