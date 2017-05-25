import tornado.web

import constants
import matchmaking


class MatchmakingView(tornado.web.RequestHandler):

    # noinspection PyMethodOverriding
    def initialize(self, manager):
        self.manager = manager

    def get(self):
        self.render('matchmaking.html', gamemodes=self.manager.gamemodes)


class GameView(tornado.web.RequestHandler):

    def initialize(self):
        pass

    def post(self):
        pass