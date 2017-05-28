import logging
import tornado.web

import constants
import matchmaking


log = logging.getLogger(__name__)


class MatchmakingView(tornado.web.RequestHandler):

    # noinspection PyMethodOverriding
    def initialize(self, manager):
        self.manager = manager

    def get(self):
        self.render('matchmaking.html', gamemodes=self.manager.gamemodes)


class GameView(tornado.web.RequestHandler):

    # noinspection PyMethodOverriding
    def initialize(self, manager):
        self.manager = manager
        self.game_inst = None

    def post(self, *args, **kwargs):
        try:
            self.render('game.html', socket_url='socket/game', token=str(self.request.arguments['token'][0], encoding='utf-8'))
        except KeyError:
            self.send_error(400)
            log.warning('client %s did not send a token', self.request.remote_ip)
            return
