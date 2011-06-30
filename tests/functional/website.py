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
    application.listen(int(sys.argv[1]), '0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()
