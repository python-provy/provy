Running provy
=============

*provy* comes with a console runner. It's the same one we used in the `Getting started`_ tutorial.

The console runner supports some options. For more information you can use the --help command. You should see output like the following::

    $ provy --help
    Usage: console.py [options]
     
    Options:
      -h, --help            show this help message and exit
      -s SERVER, --server=SERVER
                            Servers to provision with the specified role. This is
                            a recursive     option.
      -p PASSWORD, --password=PASSWORD
                            Password to use for authentication with servers.
                            If passwords differ from server to server this does
                            not work.

The option you are most likely to use is the *server* option. It tells *provy* what servers you want provisioned.

As we saw in the `provyfile and Runtime Arguments`_ section, we can also supply *AskFor* arguments when running *provy*.

All arguments must take the form of key=value, with no spaces. The key must be exactly the same as the one in the *AskFor* definition, case-sensitive.