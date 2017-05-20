"""
Main server file. The server is run with this.
"""
import logging
import os

import tornado.ioloop

import constants
import matchmaking
import sockets
import threadmanager

PATH = os.getcwd()


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG if constants.DEBUG_MODE else logging.INFO)


class MatchmakingPage(tornado.web.RequestHandler):

    def initialize(self, gamemodes):
        self.gamemodes = gamemodes

    def get(self):
        self.render('matchmaking.html', gamemodes=self.gamemodes)


def get_app():

    gamemodes = [
        matchmaking.Gamemode('Duel', 'duel', 2, 1),
        matchmaking.Gamemode('3-player FFA', 'ffa3', 3, 1),
        matchmaking.Gamemode('3-player FFA', 'ffa6', 6, 1),
        matchmaking.Gamemode('3-player FFA', 'ffa10', 10, 1),
        matchmaking.Gamemode('3v3 TDM', 'tdm3', 2, 3),
        matchmaking.Gamemode('5v5 TDM', 'tdm5', 2, 3),
    ]

    thread_man = threadmanager.ThreadsManager(10, 5, constants.UPDATE_PERIOD)
    mmers = [matchmaking.Matchmaker(gm, constants.MM_UPDATE_PERIOD, thread_man) for gm in gamemodes]

    for mm in mmers:
        mm.begin()

    return tornado.web.Application([
        (r'/', MatchmakingPage, {'gamemodes': gamemodes}),
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(PATH, '../static')}),
        (r'/socket/matchmaking', sockets.LobbyPlayerConnection, {'mmers': mmers})
    ], template_path='../views')


if __name__ == "__main__":
    app = get_app()
    log.info('Starting server')
    app.listen(80)
    tornado.ioloop.IOLoop.current().start()
