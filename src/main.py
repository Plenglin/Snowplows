"""
Main server file. The server is run with this.
"""
import logging
import os

import tornado.ioloop
import tornado.web

import constants
import matchmaking
import sockets
import threadmanager
import views

PATH = os.getcwd()
GAMEMODES = [
    matchmaking.Gamemode('Duel', 'duel', 2, 1),
    matchmaking.Gamemode('3-player FFA', 'ffa3', 3, 1),
    matchmaking.Gamemode('6-player FFA', 'ffa6', 6, 1),
    matchmaking.Gamemode('10-player FFA', 'ffa10', 10, 1),
    matchmaking.Gamemode('3v3 TDM', 'tdm3', 2, 3),
    matchmaking.Gamemode('5v5 TDM', 'tdm5', 2, 5),
]

log = logging.getLogger(__name__)


class GameManager:

    def __init__(self, gamemodes,
                 threads_update_period=constants.ID_LENGTH, matchmaking_update_period=constants.MM_UPDATE_PERIOD):
        self.gamemodes = gamemodes

        self.thread_man = threadmanager.ThreadsManager(10, 5, threads_update_period)
        self.mmers = [matchmaking.Matchmaker(gm, matchmaking_update_period, self) for gm in gamemodes]

        self.tokens = {}

    def init(self):
        for mm in self.mmers:
            mm.init()


def get_app():

    manager = GameManager(GAMEMODES)
    manager.init()

    return tornado.web.Application([

        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(PATH, '../static')}),

        (r'/', views.MatchmakingView, {'manager': manager}),
        (r'/game', views.GameView, {'manager': manager}),

        (r'/socket/matchmaking', sockets.LobbyPlayerConnection, {'manager': manager}),
        (r'/socket/game', sockets.GamePlayerConnection, {'manager': manager, 'transmission_pd': constants.GAME_TRANSMISSION_PERIOD}),

    ], template_path='../views')


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG if constants.DEBUG_MODE else logging.INFO)
    log.info('starting server...')
    app = get_app()
    app.listen(constants.PORT)
    log.info('server listening on port %s', constants.PORT)
    tornado.ioloop.IOLoop.current().start()
