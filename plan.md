How rooms are to be run
=======================
There will be a thread pool. (i.e. 20-50 threads)

Each thread will run multiple games asynchronously. (i.e. 5-10 games)

This allows for speed and maximum thread utilization at the same time.


Matchmaking
===========
Matchmaking will be based on space availability and whether there are enough players.

If the servers are full, there will be waits.

Bot players will be added if there are no humans after a certain amount of time. (i.e. 15 sec)

Player Accounts
===============
Possibility.

Textures
========
Last priority.

Gamemodes
=========
- FFA
    - [ ] 3 player
    - [ ] 6 player
    - [ ] 10 player
- TDM
    - [ ] 3v3 Team Deathmatch
    - [ ] 5v5 Team Deathmatch
- [ ] 2-player duel
- [ ] Developer mode (hidden from others)
- [ ] Custom game
- Possible gamemodes (warning: involves respawning)?
    - [ ] CTF
    - [ ] KOTH

Map Types
=========
- [ ] Rectangular
- [ ] N-hole Donut
- [ ] "Urban"