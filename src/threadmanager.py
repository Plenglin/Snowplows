"""
The code that manages all the multiple threads and games per thread.
"""
import asyncio
import threading
import time

import game


class ThreadsManager:
    """
    Manages a group of threads and properly places games in each thread.
    """

    def __init__(self, thread_limit, games_per_thread, update_period):
        self.threads = []
        self.thread_limit = thread_limit
        self.games_per_thread = games_per_thread
        self.update_period = update_period

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

    def create_thread(self):
        """
        Create a thread. This ignores can_create_thread.
        :return:
        """
        thread = RoomCluster(self.games_per_thread, self.update_period)
        self.threads.append(thread)
        return thread

    def next_thread_or_create(self):
        """
        Finds the next thread with an empty space. If there are none, checks if we can make a new thread. If we can,
        creates one and returns it. Otherwise, returns None.
        :return:
        """
        thr = self.next_available_thread()
        if thr is None and self.can_create_thread():
            return self.create_thread()
        return thr

    def create_game(self):
        """
        Creates a game instance. Returns a tuple in the form of (game, thread). If there are no open slots, raises
        FullError.
        :return: 
        """
        thr = self.next_thread_or_create()
        if thr is None:
            raise FullError
        return thr.create_instance(), thr

    def create_room(self):
        """
        Creates a new game and returns it if it could do so. Raises a FullError if it could not.
        :return:
        """
        thr = self.next_thread_or_create()
        if thr is not None:
            return thr.create_instance()
        raise FullError


class RoomCluster(threading.Thread):
    """
    A single thread. It may run multiple games.
    """

    def __init__(self, games_limit, update_period):
        super(RoomCluster, self).__init__()
        self.games = []
        self.games_limit = games_limit
        self.event_loop = asyncio.new_event_loop()
        self.update_period = update_period

    def run(self):
        while True:
            loop_start = time.time()
            for instance in self.games:
                instance.update(self.update_period)
            try:
                time.sleep(self.update_period + loop_start - time.time())  # The amount of time remaining in this loop
            except ValueError:
                time.sleep(self.update_period)

    def can_add_game(self):
        """
        Do we have enough space to add a new game?
        :return:
        """
        return len(self.games) < self.games_limit

    def create_instance(self):
        """
        Create a new game instance and return it. Raises a FullError if it could not.
        :return:
        """
        if self.can_add_game():
            game_instance = game.GameInstance()
            self.games.append(game_instance)
            return game_instance
        raise FullError


class FullError(Exception):
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
        except FullError:
            inst, thr = None, None
        print(i, inst, thr)
