"""
The code that manages matchmaking and custom games.
"""
import logging
import queue

import tornado.ioloop

import constants
import game
import threadmanager
import util

log = logging.getLogger('matchmaking')


class LobbyPlayer:

    def __init__(self, socket, gamemode):
        self.socket = socket
        self.id = util.random_string(constants.MM_ID_LENGTH)
        self.gamemode = None

    def notify_enough_players(self):
        self.socket.on_enough_players()


class Gamemode:

    def __init__(self, name: str, code: str, team_count: int, players_per_team: int):
        self.name = name
        self.code = code
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
        return []


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
        self._periodic_callback = tornado.ioloop.PeriodicCallback(self.fill_game, self.update_period)

    def __str__(self):
        return 'Matchmaker({})'.format(self.gamemode)

    def player_count(self):
        return self.players.qlen()

    def begin(self):
        self._periodic_callback.start()

    def add_player(self, player):
        self.players.put(player)

    def fill_game(self):
        player_count = self.players.qsize()
        if player_count >= self.gamemode.total_players:
            log.info('%s has enough players (%s/%s) for a new game', self, player_count, self.gamemode.total_players)
            try:
                game = self.thread_man.create_game()
                filled_players = self.gamemode.fill_game(self.players, game)
            except threadmanager.OutOfSpaceError:
                log.info('%s could not create game because there are not enough slots.', self)

log.setLevel(logging.DEBUG if constants.DEBUG_MODE else logging.INFO)
