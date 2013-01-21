Getting started
===============

Starting to provision servers with *provy* is extremely simple. We'll provision a fairly scalable infrastructure (yet simple) for a `Tornado <http://tornadoweb.org/>`_ website.

`Tornado <http://tornadoweb.org/>`_ is facebook's python web server. It features non-blocking I/O and is extremely fast.

The solution
------------

Below you can see a diagram of our solution:

.. image:: images/provy_sample.png

Our solution will feature a front-end server with `one nginx instance <http://www.nginx.org/>`_ doing the load-balancing among the `tornado <http://tornadoweb.org/>`_ instances in our back-end server.

The back-end server will feature 4 `tornado <http://tornadoweb.org/>`_ instances kept alive by `supervisor <http://supervisord.org/>`_ (a process monitoring tool).

Create a file called *website.py* at some directory with this contents:

Yes, it is not a very involved example, but *Hello World* suffices for our purposes. This python application takes a port as command-line argument and can be run with:

The servers
-----------

Ok, now that we have a functioning application, let's deploy it to production.

First, let's create a local "production" environment using `Vagrant <http://vagrantup.com/>`_. Using `Vagrant <http://vagrantup.com/>`_ is beyond the scope of this tutorial.

First make sure you have the *base* box installed. If you don't, use:

In the same directory that we created the website.py file, type:

This will create a file called VagrantFile. This is the file that configures our `Vagrant <http://vagrantup.com/>`_ instances. Open it up in your editor of choice and change it to read:

Ok, now when we run vagrant we'll have two servers up: 33.33.33.33 and 33.33.33.34. The first one will be our front-end server and the latter our back-end server.

Provisioning file
-----------------

It's now time to start provisioning our servers. In the same directory that we created the *website.py* file, let's create a file called *provyfile.py*.

The first thing we'll do in this file is importing the *provy* classes we'll use. We'll also define *FrontEnd* and *BackEnd* roles and assign them to our two vagrant servers.

Even though our script does not actually provision anything yet, let's stop to see some interesting points of it.

You can see that our roles (*FrontEnd* and *BackEnd*) both inherit from *provy.Role*. This is needed so that these roles can inherit a lot of functionality needed for interacting with our servers.

Another thing to notice is the *servers* dictionary. This is where we tell *provy* how to connect to each server and what roles does it have.

We can run this script (even if it won't do anything) with:

Provisioning the back-end server
--------------------------------

Let's start working in our back-end server, since our front-end server depends on it to run.

First we'll make sure we are running our app under our own user and not root:

Then we'll need to copy the *website.py* file to the server. *provy* can easily copy files to the servers, as long as it can find them. Just move the *website.py* file to a directory named *files* in the same directory as *provyfile.py*.

Now we can easily copy it to the */home/frontend* directory:

The *update_file* method tells *provy* to compare the source and target files and if they are different update the target file. For more information check the documentation.

Next we must make sure `Tornado <http://tornadoweb.org/>`_ is installed. *provy* already comes with a role that does that:

Now all we have to do is instruct supervisor to run four instances of our app:

Provisioning the front-end server
---------------------------------

Ok, now let's get our front-end up and running. *provy* comes with an `nginx <http://www.nginx.org/>`_ module, so it is pretty easy configuring it.

We have to provide template files for both *nginx.conf* and our website's site. Following what `Tornado <http://tornadoweb.org/>`_'s documentation instructs, these are good templates:

Save them as *files/nginx.conf* and *files/website*, respectively.

Now all that's left is making sure that *provy* configures our front-end server:

See how we passed the user name as an option to the *nginx.conf* template? *provy* allows this kind of template interaction in many places. For more information, check the documentation.

Running and verifying it works
------------------------------

We can now fire our brand new infrastructure and check that the website is working:

After these 3 commands finished running (it might take a long time depending on your connection speed), you should see *Hello World* as the result of the curl command.