import logging

from tornado import websocket

import constants
import matchmaking

INITIAL = 0
FINDING = 1
FILLING = 2


class LobbyPlayerConnection(websocket.WebSocketHandler):

    log = logging.getLogger('LobbySocket')

    # noinspection PyMethodOverriding
    def initialize(self, mmers):
        self.mmers = mmers
        self.state = INITIAL
        self.gamemode = None

    def open(self, *args, **kwargs):
        self.log.debug('client connected from IP %s', self.request.remote_ip)

    def on_message(self, msg):
        if self.state == INITIAL:
            try:
                self.mmer = [mmer for mmer in self.mmers if mmer.gamemode.code == msg][0]
                self.log.info('%s requests gamemode %s', self.request.remote_ip, msg)
                self.lobby_player = matchmaking.LobbyPlayer(self, self.mmer.gamemode)
                self.mmer.add_player(self.lobby_player)
                self.log.debug('%s assigned id %s', self.request.remote_ip, self.lobby_player.id)
                self.write_message(bytes(self.lobby_player.id, encoding='utf-8'))
            except IndexError:
                self.log.warning('%s sent invalid gamemode %s', self.request.remote_ip, msg)
                self.close(1002, 'Invalid gamemode')
        elif self.state == FINDING:
            pass
        elif self.state == FILLING:
            pass

    def on_close(self):
        pass

    def player_added(self):
        pass


LobbyPlayerConnection.log.setLevel(logging.DEBUG if constants.DEBUG_MODE else logging.WARN)