import json
import logging
import enum

import tornado
import tornado.ioloop
from tornado import websocket

import constants
import matchmaking


class LobbyState(enum.Enum):
    INITIAL = 0
    FINDING = 1
    FILLING = 2


class GameState(enum.Enum):
    OPENING = 0
    GAME = 1
    CLOSING = 2


class LobbyPlayerConnection(websocket.WebSocketHandler):

    log = logging.getLogger('LobbySocket')

    # noinspection PyMethodOverriding
    def initialize(self, mmers):
        self.mmers = mmers
        self.state = LobbyState.INITIAL
        self.gamemode = None
        self.queue_notifier = None

    def open(self, *args, **kwargs):
        self.log.debug('client connected from IP %s', self.request.remote_ip)

    def on_message(self, msg):
        if self.state == LobbyState.INITIAL:

            try:
                self.mmer = [mmer for mmer in self.mmers if mmer.gamemode.code == msg][0]
                self.log.info('%s requests gamemode %s', self.request.remote_ip, msg)
            except IndexError:
                self.log.warning('%s sent invalid gamemode %s', self.request.remote_ip, msg)
                self.close(1002, 'Invalid gamemode')
                return

            self.lobby_player = matchmaking.LobbyPlayer(self, self.mmer.gamemode, constants.ID_LENGTH)
            self.mmer.add_player(self.lobby_player)
            self.log.info('%s assigned id %s', self.request.remote_ip, self.lobby_player.id)
            self.write_message(bytes(self.lobby_player.id, encoding='utf-8'))

            self.log.debug('starting queue length notification for %s', self.lobby_player.id)
            self.queue_notifier = tornado.ioloop.PeriodicCallback(self.notify_player_count, 5)
            self.queue_notifier.start()

        elif self.state == LobbyState.FINDING:
            pass

        elif self.state == LobbyState.FILLING:
            pass
        else:
            raise ValueError

    def notify_player_count(self):
        count = self.mmer.player_count()
        self.log.debug('notifying %s about player queue', self.lobby_player.id)
        self.write_message(bytes(json.dumps({'count': count, 'enough': False})))

    def on_close(self):
        pass

    def on_enough_players(self):
        self.log.debug('notifying %s about enough players', self.lobby_player.id)
        self.write_message(bytes(json.dumps({'count': 0, 'enough': True})))
        self.queue_notifier.stop()
        self.state = LobbyState.FILLING


class GamePlayerConnection(websocket.WebSocketHandler):

    def initialize(self):
        self.state = GameState.OPENING

    def on_message(self, msg):
        data = json.loads(msg)
        if self.state == GameState.OPENING:
            pass
        elif self.state == GameState.GAME:
            pass
        elif self.state == GameState.CLOSING:
            pass
        else:
            raise ValueError

LobbyPlayerConnection.log.setLevel(logging.DEBUG if constants.DEBUG_MODE else logging.WARN)
