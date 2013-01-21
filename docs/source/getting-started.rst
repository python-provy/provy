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

Create a file called *website.py* at some directory with this content::

    #!/usr/bin/python
    # -*- coding: utf-8 -*-
 
    import sys
    import tornado.ioloop
    import tornado.web
 
    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            self.write("Hello, world")
 
    application = tornado.web.Application([
        (r"/", MainHandler),
    ])
 
    if __name__ == "__main__":
        port = int(sys.argv[1])
        application.listen(port, '0.0.0.0')
        print ">> Website running at http://0.0.0.0:%d" % port
        tornado.ioloop.IOLoop.instance().start()

Yes, it is not a very involved example, but *Hello World* suffices for our purposes. This python application takes a port as command-line argument and can be run with::

    $ python website.py 8000 
    >> Website running at http://0.0.0.0:8000

The servers
-----------

Ok, now that we have a functioning application, let's deploy it to production.

First, let's create a local "production" environment using `Vagrant <http://vagrantup.com/>`_. Using `Vagrant <http://vagrantup.com/>`_ is beyond the scope of this tutorial.

First make sure you have the *base* box installed. If you don't, use::

    $ vagrant box add base http://files.vagrantup.com/lucid32.box

In the same directory that we created the website.py file, type::

    $ vagrant init
          create  Vagrantfile

This will create a file called VagrantFile. This is the file that configures our `Vagrant <http://vagrantup.com/>`_ instances. Open it up in your editor of choice and change it to read::

    Vagrant::Config.run do |config|
 
        config.vm.define :frontend do |inner_config|
            inner_config.vm.box = "base"
            inner_config.vm.forward_port(80, 8080)
            inner_config.vm.network(:hostonly, "33.33.33.33")
        end
 
        config.vm.define :backend do |inner_config|
            inner_config.vm.box = "base"
            inner_config.vm.forward_port(80, 8081)
            inner_config.vm.network(:hostonly, "33.33.33.34")
        end
 
    end

Ok, now when we run vagrant we'll have two servers up: 33.33.33.33 and 33.33.33.34. The first one will be our front-end server and the latter our back-end server.

Provisioning file
-----------------

It's now time to start provisioning our servers. In the same directory that we created the *website.py* file, let's create a file called *provyfile.py*.

The first thing we'll do in this file is importing the *provy* classes we'll use. We'll also define *FrontEnd* and *BackEnd* roles and assign them to our two vagrant servers. ::

    #!/usr/bin/python
    # -*- coding: utf-8 -*-
 
    from provy.core import Role
 
    class FrontEnd(Role):
        def provision(self):
            pass
 
    class BackEnd(Role):
        def provision(self):
            pass
 
    servers = {
        'test': {
            'frontend': {
                'address': '33.33.33.33',
                'user': 'vagrant',
                'roles': [
                    FrontEnd
                ]
            },
            'backend': {
                'address': '33.33.33.34',
                'user': 'vagrant',
                'roles': [
                    BackEnd
                ]
            }
        }
    }

Even though our script does not actually provision anything yet, let's stop to see some interesting points of it.

You can see that our roles (*FrontEnd* and *BackEnd*) both inherit from *provy.Role*. This is needed so that these roles can inherit a lot of functionality needed for interacting with our servers.

Another thing to notice is the *servers* dictionary. This is where we tell *provy* how to connect to each server and what roles does it have.

We can run this script (even if it won't do anything) with::

    $ # will provision both servers
    $ provy -s test
 
    $ # will provision only the frontend server
    $ provy -s test.frontend
 
    $ # will provision only the backend server
    $ provy -s test.backend

Provisioning the back-end server
--------------------------------

Let's start working in our back-end server, since our front-end server depends on it to run.

First we'll make sure we are running our app under our own user and not root::

    #!/usr/bin/python
    # -*- coding: utf-8 -*-
 
    from provy.core import Role
    from provy.more.debian import UserRole
 
    class FrontEnd(Role):
        def provision(self):
            pass
 
    class BackEnd(Role):
        def provision(self):
            with self.using(UserRole) as role:
                role.ensure_user('backend', identified_by='pass', is_admin=True)
 
    servers = {
        'test': {
            'frontend': {
                'address': '33.33.33.33',
                'user': 'vagrant',
                'roles': [
                    FrontEnd
                ]
            },
            'backend': {
                'address': '33.33.33.34',
                'user': 'vagrant',
                'roles': [
                    BackEnd
                ]
            }
        }
    }

Then we'll need to copy the *website.py* file to the server. *provy* can easily copy files to the servers, as long as it can find them. Just move the *website.py* file to a directory named *files* in the same directory as *provyfile.py*.

Now we can easily copy it to the */home/frontend* directory::

    #!/usr/bin/python
    # -*- coding: utf-8 -*-
 
    from provy.core import Role
    from provy.more.debian import UserRole
 
    class FrontEnd(Role):
        def provision(self):
            pass
 
    class BackEnd(Role):
        def provision(self):
            with self.using(UserRole) as role:
                role.ensure_user('backend', identified_by='pass', is_admin=True)
 
            self.update_file('website.py', '/home/backend/website.py', owner='backend', sudo=True)
 
    servers = {
        'test': {
            'frontend': {
                'address': '33.33.33.33',
                'user': 'vagrant',
                'roles': [
                    FrontEnd
                ]
            },
            'backend': {
                'address': '33.33.33.34',
                'user': 'vagrant',
                'roles': [
                    BackEnd
                ]
            }
        }
    }

The *update_file* method tells *provy* to compare the source and target files and if they are different update the target file. For more information check the documentation.

Next we must make sure `Tornado <http://tornadoweb.org/>`_ is installed. *provy* already comes with a role that does that::

    #!/usr/bin/python
    # -*- coding: utf-8 -*-
 
    from provy.core import Role
    from provy.more.debian import UserRole, TornadoRole
 
    class FrontEnd(Role):
        def provision(self):
            pass
 
    class BackEnd(Role):
        def provision(self):
            with self.using(UserRole) as role:
                role.ensure_user('backend', identified_by='pass', is_admin=True)
 
            self.update_file('website.py', '/home/backend/website.py', owner='backend', sudo=True)
 
            self.provision_role(TornadoRole)
 
    servers = {
        'test': {
            'frontend': {
                'address': '33.33.33.33',
                'user': 'vagrant',
                'roles': [
                    FrontEnd
                ]
            },
            'backend': {
                'address': '33.33.33.34',
                'user': 'vagrant',
                'roles': [
                    BackEnd
                ]
            }
        }
    }

Now all we have to do is instruct supervisor to run four instances of our app::

    #!/usr/bin/python
    # -*- coding: utf-8 -*-
 
    from provy.core import Role
    from provy.more.debian import UserRole, TornadoRole, SupervisorRole
 
    class FrontEnd(Role):
        def provision(self):
            pass
 
    class BackEnd(Role):
        def provision(self):
            with self.using(UserRole) as role:
                role.ensure_user('backend', identified_by='pass', is_admin=True)
 
            self.update_file('website.py', '/home/backend/website.py', owner='backend', sudo=True)
 
            self.provision_role(TornadoRole)
 
            # make sure we have a folder to store our logs
            self.ensure_dir('/home/backend/logs', owner='backend')
 
            with self.using(SupervisorRole) as role:
                role.config(
                    config_file_directory='/home/backend',
                    log_folder='/home/backend/logs/',
                    user='backend'
                )
 
                with role.with_program('website') as program:
                    program.directory = '/home/backend'
                    program.command = 'python website.py 800%(process_num)s'
                    program.number_of_processes = 4
 
                    program.log_folder = '/home/backend/logs'
 
    servers = {
        'test': {
            'frontend': {
                'address': '33.33.33.33',
                'user': 'vagrant',
                'roles': [
                    FrontEnd
                ]
            },
            'backend': {
                'address': '33.33.33.34',
                'user': 'vagrant',
                'roles': [
                    BackEnd
                ]
            }
        }
    }

Provisioning the front-end server
---------------------------------

Ok, now let's get our front-end up and running. *provy* comes with an `nginx <http://www.nginx.org/>`_ module, so it is pretty easy configuring it.

We have to provide template files for both *nginx.conf* and our website's site. Following what `Tornado <http://tornadoweb.org/>`_'s documentation instructs, these are good templates::

    user {{ user }};
    worker_processes 1;
     
    error_log /home/frontend/error.log;
    pid /home/frontend/nginx.pid;
     
    events {
        worker_connections 1024;
        use epoll;
    }
     
    http {
        include /etc/nginx/mime.types;
        default_type application/octet-stream;
     
        access_log /home/frontend/nginx.access.log;
     
        keepalive_timeout 65;
        proxy_read_timeout 200;
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        gzip on;
        gzip_min_length 1000;
        gzip_proxied any;
        gzip_types text/plain text/css text/xml
                   application/x-javascript application/xml
                   application/atom+xml text/javascript;
     
        proxy_next_upstream error;
     
        include /etc/nginx/conf.d/*.conf;
        include /etc/nginx/sites-enabled/*;
    }

::

    upstream frontends {
        server 33.33.33.34:8000;
        server 33.33.33.34:8001;
        server 33.33.33.34:8002;
        server 33.33.33.34:8003;
    }
     
    server {
        listen 8888;
        server_name  localhost 33.33.33.33;
     
        access_log  /home/frontend/website.access.log;
     
        location / {
            proxy_pass_header Server;
            proxy_set_header Host $http_host;
            proxy_redirect off;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Scheme $scheme;
            proxy_pass http://frontends;
        }
    }

Save them as *files/nginx.conf* and *files/website*, respectively.

Now all that's left is making sure that *provy* configures our front-end server::

    #!/usr/bin/python
    # -*- coding: utf-8 -*-
     
    from provy.core import Role
    from provy.more.debian import UserRole, TornadoRole, SupervisorRole, NginxRole
     
    class FrontEnd(Role):
        def provision(self):
            with self.using(UserRole) as role:
                role.ensure_user('frontend', identified_by='pass', is_admin=True)
     
            with self.using(NginxRole) as role:
                role.ensure_conf(conf_template='nginx.conf', options={'user': 'frontend'})
                role.ensure_site_disabled('default')
                role.create_site(site='website', template='website')
                role.ensure_site_enabled('website')
     
    class BackEnd(Role):
        def provision(self):
            with self.using(UserRole) as role:
                role.ensure_user('backend', identified_by='pass', is_admin=True)
     
            self.update_file('website.py', '/home/backend/website.py', owner='backend', sudo=True)
     
            self.provision_role(TornadoRole)
     
            # make sure we have a folder to store our logs
            self.ensure_dir('/home/backend/logs', owner='backend')
     
            with self.using(SupervisorRole) as role:
                role.config(
                    config_file_directory='/home/backend',
                    log_folder='/home/backend/logs/',
                    user='backend'
                )
     
                with role.with_program('website') as program:
                    program.directory = '/home/backend'
                    program.command = 'python website.py 800%(process_num)s'
                    program.number_of_processes = 4
     
                    program.log_folder = '/home/backend/logs'
     
    servers = {
        'test': {
            'frontend': {
                'address': '33.33.33.33',
                'user': 'vagrant',
                'roles': [
                    FrontEnd
                ]
            },
            'backend': {
                'address': '33.33.33.34',
                'user': 'vagrant',
                'roles': [
                    BackEnd
                ]
            }
        }
    }

See how we passed the user name as an option to the *nginx.conf* template? *provy* allows this kind of template interaction in many places. For more information, check the documentation.

Running and verifying it works
------------------------------

We can now fire our brand new infrastructure and check that the website is working::

    $ vagrant up
    $ provy -s test
    $ curl http://33.33.33.33

After these 3 commands finished running (it might take a long time depending on your connection speed), you should see *Hello World* as the result of the curl command.