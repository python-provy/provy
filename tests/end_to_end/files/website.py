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
