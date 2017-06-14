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

    def __init__(self, socket, gamemode, id_len):
        self.socket = socket
        self.id = util.random_string(id_len)
        self.gamemode: Gamemode = gamemode


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

    def fill_game(self, players, inst: game.GameInstance):
        out = []
        for t in range(self.team_count):
            team = inst.create_team()
            for p in range(self.players_per_team):
                lobby_player = players.get()
                game_player = team.create_player()
                out.append((lobby_player, game_player))
        return out


class Matchmaker:
    """
    Handles the matchmaking for a single gamemode
    """

    def __init__(self, gamemode: Gamemode, update_period: float, manager):
        self.update_period = update_period
        self.gamemode = gamemode
        self.manager = manager

        self.next_id = 0
        self.players = queue.Queue()
        self._periodic_callback = tornado.ioloop.PeriodicCallback(self.fill_game, self.update_period)

    def __repr__(self):
        return 'Matchmaker({})'.format(self.gamemode)

    def player_count(self):
        return self.players.qsize()

    def init(self):
        log.debug('initializing %s', self)
        self._periodic_callback.start()

    def add_player(self, player):
        self.players.put(player)

    def fill_game(self):
        player_count = self.players.qsize()
        if player_count >= self.gamemode.total_players:
            log.info('%s has enough players (%s/%s) for a new game', self, player_count, self.gamemode.total_players)
            try:
                game_id, room_cluster = self.manager.thread_man.create_game()
                inst = self.manager.thread_man.get_game(game_id)
                log.debug('created game with id %s', game_id)
                filled_players = self.gamemode.fill_game(self.players, inst)
                for lob, player in filled_players:
                    token = util.random_string(constants.ID_LENGTH)
                    self.manager.tokens[token] = game_id, player.id
                    lob.socket.on_enough_players(token)

            except threadmanager.OutOfSpaceError:
                log.info('%s could not create game because there are not enough slots.', self)
