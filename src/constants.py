import os

# How long between pings before a player is considered disconnected
TIMEOUT = 10 # NYI

# Matchmaking Parameters
PEOPLE_PER_GAME = 2  # TODO: CHANGE THIS BACK WHEN DONE DEBUGGING
MM_UPDATE_PERIOD = 1
ID_LENGTH = 16

# Misc
DEV_TOKEN = 'horscho'

# Environment Variables
DEBUG_MODE = bool(int(os.environ.get('DEBUG', 0)))
PORT = int(os.environ.get('PORT', 8080))
