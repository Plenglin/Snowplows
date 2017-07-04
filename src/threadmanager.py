"""
The code that manages all the multiple threads and games per thread.
"""
import asyncio
import logging
import threading
import time

import constants
import game
import util

log = logging.getLogger(__name__)


class ThreadsManager:
    """
    Manages a group of threads and properly places games in each thread.
    """

    def __init__(self, thread_limit, games_per_thread, update_period):
        """
        :param thread_limit: most number of threads this can make 
        :param games_per_thread: how many games will we allow in each thread?
        :param update_period: delay between updates in seconds
        """
        self.thread_limit = thread_limit
        self.games_per_thread = games_per_thread
        self.update_period = update_period

        self.threads = []
        self.game_registry = {}

    def __repr__(self):
        return 'ThreadsManager({})'.format(id(self))

    def games(self):
        for t in self.threads:
            for g in t:
                yield g

    def next_available_thread(self):
        """
        Find the next thread with an empty slot
        :return:
        """
        for th in self.threads:
            if th.can_add_game():
                return th
        return None

    def can_create_thread(self):
        """
        Can we create a new thread?
        :return:
        """
        return len(self.threads) < self.thread_limit

    def _create_thread(self):
        """
        Create a thread. This ignores can_create_thread.
        :return:
        """
        log.debug('%s creating new thread', self)
        thread = RoomCluster(self.games_per_thread, constants.GAME_UPDATE_PERIOD)
        thread.start()
        self.threads.append(thread)
        return thread

    def next_thread_or_create(self):
        """
        Finds the next thread with an empty space. If there are none, checks if we can make a new thread. If we can,
        creates one and returns it. Otherwise, returns None.
        :return:
        """
        log.debug('%s finding next thread')
        thr = self.next_available_thread()
        if thr is None and self.can_create_thread():
            return self._create_thread()
        return thr

    def create_game(self):
        """
        Creates a game instance. Returns a tuple in the form of (game, thread). If there are no open slots, raises
        FullError.
        :return: 
        """
        log.debug('%s attempting to create new game')
        thr = self.next_thread_or_create()
        if thr is None:
            log.debug('%s could not create game, raising error')
            raise OutOfSpaceError
        game_id = util.random_string(constants.ID_LENGTH)
        game = thr.create_instance(game_id)
        self.game_registry[game_id] = game
        return game_id, thr

    def get_game(self, id: str):
        return self.game_registry[id]

    def remove_game(self, id: str):
        game = self.game_registry[id]
        for t in self.threads:
            for g in t:
                if g is game:
                    del self.game_registry[id]
                    break
            else:
                break
        else:
            raise LookupError('game_registry and actual contents do not match')


class RoomCluster(threading.Thread):
    """
    A single thread. It may run multiple games.
    """

    def __init__(self, games_limit, update_period):
        super().__init__()
        self.games = []
        self.games_limit = games_limit
        self.event_loop = asyncio.new_event_loop()
        self.update_period = update_period

    def __iter__(self):
        for g in self.games:
            yield g

    def run(self):
        log.debug('%s starting', self)
        while True:
            loop_start = time.time()
            for instance in self.games:
                # log.debug('running %s', instance)
                instance.update(self.update_period)
            delay_time = self.update_period + loop_start - time.time()
            try:
                time.sleep(delay_time)  # The amount of time remaining in this loop
            except ValueError:
                log.warning('%s is lagging behind schedule!', self)
                pass

    def can_add_game(self):
        """
        Do we have enough space to add a new game?
        :return:
        """
        return len(self.games) < self.games_limit

    def create_instance(self, g_id) -> game.GameInstance:
        """
        Create a new game instance and return it. Raises a FullError if it could not.
        :return:
        """
        if self.can_add_game():
            game_instance = game.GameInstance(g_id)
            self.games.append(game_instance)
            return game_instance
        raise OutOfSpaceError


class OutOfSpaceError(Exception):
    """
    Thrown when something is too full.
    """
    pass


if __name__ == '__main__':
    # Test the functionality of the thread manager.
    man = ThreadsManager(2, 5, 1)
    for i in range(0, 30):
        try:
            inst, thr = man.create_game()
        except OutOfSpaceError:
            inst, thr = None, None
        print(i, inst, thr)
