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
        self.render('html/game.html')


def add_4(data, shared):
    data['foo'] += 4
    return data

router = eventsocket.EventSocketRouter()

router.on_open = lambda s: eventsocket.Sequence('test', s, [add_4, add_4]).register().begin({'foo': 9})

app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(PATH, '../static')}),
    (r'/sockets/matchmaking/(.*)', eventsocket.EventSocketHandler, {'router': router})
], template_path='../templates')


if __name__ == "__main__":
    app.listen(80)
    logging.getLogger('eventsocket').setLevel(logging.DEBUG)
    logging.info('Starting server')
    tornado.ioloop.IOLoop.current().start()
