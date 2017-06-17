import json
import logging
import enum

import tornado
import tornado.ioloop
from tornado import websocket

import constants
import matchmaking


log = logging.getLogger(__name__)


class LobbyState(enum.Enum):
    INITIAL = 0
    FINDING = 1
    FILLING = 2


class GameState(enum.Enum):
    OPENING = 0
    GAME = 1
    CLOSING = 2


class LobbyPlayerConnection(websocket.WebSocketHandler):

    # noinspection PyMethodOverriding
    def initialize(self, manager):
        self.manager = manager
        self.state = LobbyState.INITIAL
        self.gamemode = None
        self.queue_notifier = None

    def open(self, *args, **kwargs):
        log.debug('client connected from IP %s', self.request.remote_ip)

    def on_message(self, msg):
        if self.state == LobbyState.INITIAL:

            try:
                self.mmer = [mmer for mmer in self.manager.mmers if mmer.gamemode.code == msg][0]
                log.info('%s requests gamemode %s', self.request.remote_ip, msg)
            except IndexError:
                log.warning('%s sent invalid gamemode %s', self.request.remote_ip, msg)
                self.close(1002, 'Invalid gamemode')
                return

            self.lobby_player = matchmaking.LobbyPlayer(self, self.mmer.gamemode, constants.ID_LENGTH)
            self.mmer.add_player(self.lobby_player)
            log.info('%s assigned id %s', self.request.remote_ip, self.lobby_player.id)
            self.write_message(self.lobby_player.id)

            log.debug('starting queue length notification for %s', self.lobby_player.id)
            self.queue_notifier = tornado.ioloop.PeriodicCallback(self.notify_player_count, 3000)
            self.queue_notifier.start()

        elif self.state == LobbyState.FINDING:
            pass

        elif self.state == LobbyState.FILLING:
            pass

        else:
            raise ValueError('Something went wrong with the state machine in LobbyPlayerConnection')

    def notify_player_count(self):
        count = self.mmer.player_count()
        log.debug('notifying %s about player queue', self.lobby_player.id)
        self.write_message(json.dumps({'count': count, 'enough': False}))

    def on_close(self):
        pass

    def on_enough_players(self, token:str):
        log.debug('notifying %s about enough players', self.lobby_player.id)
        self.write_message(json.dumps({'count': 0, 'enough': True, 'token': token}))
        self.queue_notifier.stop()
        self.state = LobbyState.FILLING


class GamePlayerConnection(websocket.WebSocketHandler):

    # noinspection PyMethodOverriding
    def initialize(self, manager, transmission_pd):
        self.state = GameState.OPENING
        self.manager = manager
        self.period = transmission_pd
        self.player_id = None
        self.game_inst = None
        self.outputter = None

    def on_message(self, msg):

        data = json.loads(msg)

        if self.state == GameState.OPENING:
            try:
                token = data['token']
            except KeyError:
                self.send_error(400)
                log.warning('client %s did not send a token', self.request.remote_ip)
                return
            try:
                g_id, self.player_id = self.manager.tokens[token]
                log.debug('client %s sent valid token %s', self.request.remote_ip, token)
            except KeyError:
                self.send_error(400)
                log.warning('client %s sent invalid token %s', self.request.remote_ip, token)
                return
            log.debug('client %s is in game with id %s', self.player_id, g_id)
            self.game_inst = self.manager.thread_man.get_game(g_id)
            self.player = self.game_inst.player_with_id(self.player_id)

            self.write_message(json.dumps({
                'valid': True,
                'id': self.player_id,
                'playerTeamId': self.player.team.id,
                'teamIds': [t.id for t in self.game_inst.teams]
            }))
            self.player.ready = True
            self.outputter = tornado.ioloop.PeriodicCallback(self.game_loop, self.period)
            self.outputter.start()
            self.state = GameState.GAME

        elif self.state == GameState.GAME:
            pass

        elif self.state == GameState.CLOSING:
            pass

        else:
            raise ValueError('Something went wrong with the state machine in GamePlayerConnection')

    def game_loop(self):
        encoded_data = self.game_inst.get_encoded()
        self.write_message(encoded_data)


log.setLevel(logging.DEBUG if constants.DEBUG_MODE else logging.WARN)
