"""
The code that manages matchmaking and custom games.
"""
import logging
import queue

import tornado.ioloop

from . import game
from . import eventsocket
from . import threadmanager


_logger = logging.getLogger('matchmaking')


class Matchmaker:
    """
    Handles the matchmaking for a single gamemode
    """

    def __init__(self, gamemode: Gamemode, update_period: float, thread_man: threadmanager.ThreadsManager):
        self.update_period = update_period
        self.gamemode = gamemode
        self.thread_man = thread_man

        self.next_id = 0
        self.players = queue.Queue()
        self._periodic_callback = tornado.ioloop.PeriodicCallback(self._callback, self.update_period)

    def __str__(self):
        return 'Matchmaker({})'.format(self.gamemode)

    def begin(self):
        self._periodic_callback.start()

    def _callback(self):
        player_count = self.players.qsize()
        if player_count >= self.gamemode.total_players:
            _logger.info('%s has enough players (%s/%s) for a new game', self, player_count, self.gamemode.total_players)
            try:
                game = self.thread_man.create_game()
                self.gamemode.fill_game(self.players, game)
            except threadmanager.FullError:
                _logger.info('%s could not create game because there are not enough slots.', self)


class LobbyPlayer:

    def __init__(self, socket):
        self.socket = socket
        self.id = None
        self.gamemode = None

    def get_handshake_sequence(self):

        def get_gamemode(data, shared):
            self.gamemode = data['gamemode']
            return {'playerId': self.id}

        sequence = eventsocket.Sequence('handshake', self.socket, [get_gamemode])
        return sequence


class Gamemode:

    def __init__(self, name: str, team_count: int, players_per_team: int):
        self.name = name
        self.team_count = team_count
        self.players_per_team = players_per_team

    def __str__(self):
        if self.players_per_team == 1:
            return '{}p-FFA'.format(self.team_count)
        else:
            return 'v'.join(str(self.players_per_team) for _ in range(0, self.team_count))

    @property
    def total_players(self):
        return self.team_count * self.players_per_team

    def fill_game(self, players: queue.Queue(LobbyPlayer), inst: game.GameInstance):
        # TODO: Fill this in when we have teams in games
        pass


def get_matchmaker_router():
    router = eventsocket.EventSocketRouter()

    def connect(sock):
        player = LobbyPlayer(sock)
        player.get_handshake_sequence().register()

    router.on_open = connect
