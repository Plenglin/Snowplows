import os

# How long between pings before a player is considered disconnected
TIMEOUT = 10  # NYI

# Matchmaking Parameters
MM_UPDATE_PERIOD = 1000
ID_LENGTH = 16

# Misc
DEV_TOKEN = 'horscho'

# Environment Variables
DEBUG_MODE = bool(int(os.environ.get('DEBUG', 0)))
PORT = int(os.environ.get('PORT', 8080))

# Client transmission
GAME_TRANSMISSION_PERIOD = 50  # The rate to send messages at
