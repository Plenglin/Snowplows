"""
Main server file. The server is run with this.
"""
import logging
import os

import tornado

import eventsocket

PATH = os.getcwd()


class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.render('html/index.html')

matchmaking_router = eventsocket.EventSocketRouter()
matchmaking_router.register_listener('test', lambda d, s: s.emit('tooto', {'fads': 32}))

app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(PATH, '../static')}),
    (r'/sockets/matchmaking/(.*)', eventsocket.EventSocketHandler, {'router': matchmaking_router})
], template_path='../templates')


if __name__ == "__main__":
    app.listen(80)
    logging.getLogger('eventsocket').setLevel(logging.DEBUG)
    logging.info('Starting server')
    tornado.ioloop.IOLoop.current().start()
