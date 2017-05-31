from game import GameInstance


class GameManager:
    """
    Manages a single game instance.
    """

    def __init__(self, inst: GameInstance):
        self.inst = inst
        self.sockets = {}
        self.players = list(self.inst.players)

    def init_when_ready(self):
        pass

    def ready_for_init(self):
        return len(self.sockets) == len(self.players)
