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
import views

PATH = os.getcwd()
GAMEMODES = [
    matchmaking.Gamemode('Duel', 'duel', 2, 1),
    matchmaking.Gamemode('3-player FFA', 'ffa3', 3, 1),
    matchmaking.Gamemode('3-player FFA', 'ffa6', 6, 1),
    matchmaking.Gamemode('3-player FFA', 'ffa10', 10, 1),
    matchmaking.Gamemode('3v3 TDM', 'tdm3', 2, 3),
    matchmaking.Gamemode('5v5 TDM', 'tdm5', 2, 3),
]

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG if constants.DEBUG_MODE else logging.INFO)


class GameManager:

    def __init__(self, gamemodes, update_period, matchmaking_update_period):
        self.gamemodes = gamemodes

        self.thread_man = threadmanager.ThreadsManager(10, 5, update_period)
        self.mmers = [matchmaking.Matchmaker(gm, constants.MM_UPDATE_PERIOD, self.thread_man) for gm in gamemodes]

    def init(self):
        for mm in self.mmers:
            mm.begin()



def get_app():

    manager = GameManager(GAMEMODES)
    manager.init()

    return tornado.web.Application([
        (r'/', views.MatchmakingView, {'gamemodes': manager.gamemodes}),
        (r'/game', views.GameView),
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(PATH, '../static')}),
        (r'/socket/matchmaking', sockets.LobbyPlayerConnection, {'manager': manager}),
        (r'/socket/game/dev', sockets.GamePlayerConnection)
    ], template_path='../views')


if __name__ == "__main__":
    app = get_app()
    log.info('Starting server')
    app.listen(80)
    tornado.ioloop.IOLoop.current().start()
