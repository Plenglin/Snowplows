"""Code that runs the actual game itself. It should be independent from the graphics, client-server interface, and
matchmaking as much as possible. """
import math
import random
import time

import pymunk
from pymunk import Vec2d
from typing import List, Iterable

import util
from .constants import *


class Player:
    """
    A single player, dead or alive
    """

    def __init__(self, player_id: str, body: pymunk.Body, team, living=True):
        self.id = player_id
        self.body = body
        self.team: Team = team
        self.living = living

        self.began_boost = 0
        self.braking = False

    def __repr__(self):
        return 'Player(id={}, living={}, team={})'.format(self.id, self.living, self.team.id)
    
    def get_encoded(self):
        return {
            'id': self.id,
            'x': self.pos.x,
            'y': self.pos.y,
            'living': self.living,
            'direction': self.rotation,
            'isBoosting': self.is_boosting(),
            'boostLevel': self.get_boost_level(),
        }

    @property
    def pos(self):
        return self.body.position

    @pos.setter
    def pos(self, val):
        self.body.position = val

    def is_boosting(self):
        return self.began_boost + BOOST_DURATION > time.time()

    def get_boost_level(self):
        if self.is_boosting():
            return 1 - min(1.0, (time.time() - self.began_boost) / BOOST_DURATION)
        else:
            return min(1.0, (time.time() - (self.began_boost + BOOST_DURATION)) / BOOST_COOLDOWN)

    @property
    def rotation(self):
        return self.body.angle

    @rotation.setter
    def rotation(self, val):
        self.body.angle = val


class Team:
    """
    A group of player(s) working together to get points
    """
    def __init__(self, game, team_id: str):
        self.game: GameInstance = game
        self.id = team_id
        self.players: List[Player] = []

    def __repr__(self):
        return 'Team(id={}, playercount={})'.format(self.id, len(self.players))

    def __iter__(self):
        for p in self.players:
            yield p

    def get_encoded(self):
        return {
            'id': self.id,
            'players': [p.get_encoded() for p in self]
        }

    def create_player(self) -> Player:
        # Create the body
        body = pymunk.Body(PLAYER_MASS, 1666)

        # Build the shapes
        front_physical = pymunk.Poly(body,
                                     util.offset_box(TRUCK_PLOW_LENGTH / 2 - TRUCK_BODY_SPACING / 2, 0,
                                                     TRUCK_PLOW_LENGTH,
                                                     TRUCK_PLOW_WIDTH), radius=2.0)
        front_physical.elasticity = 1.5
        front_physical.collision_type = TRUCK_PLOW_TYPE

        back_physical = pymunk.Poly(body, util.offset_box(-TRUCK_BODY_LENGTH / 2 - TRUCK_BODY_SPACING / 2, 0,
                                                          TRUCK_BODY_LENGTH - TRUCK_BODY_SPACING, TRUCK_BODY_WIDTH),
                                    radius=2.0)
        back_physical.elasticity = 5.0
        back_physical.collision_type = TRUCK_CORE_TYPE

        body.position = ARENA_WIDTH * random.random(), ARENA_HEIGHT * random.random()
        body.angle = 2 * math.pi * random.random()

        player_id = util.random_string(PLAYER_ID_LENGTH)

        # Add the player to the things
        self.game.space.add(body, front_physical, back_physical)
        player = Player(player_id, body, self)
        self.players.append(player)
        body.player = player

        return player


class GameInstance:
    """
    A single instance of the game. Only handles game updates and stuff. Nothing else. After all, we don't want a god
    object. Handle communication somewhere else.
    """

    def __init__(self):
        self.teams = []
        self.space = pymunk.Space()
        self.frames = 0

        # Listeners
        self.on_death = lambda p: None

    @property
    def players(self) -> Iterable[Player]:
        for t in self.teams:
            print(t)
            for p in t:
                yield p

    def init(self):

        # Create collision handlers...
        # Between a plow and a truck body
        pb_handler = self.space.add_collision_handler(TRUCK_PLOW_TYPE, TRUCK_CORE_TYPE)
        db_handler = self.space.add_collision_handler(DEAD_BODY_TYPE, TRUCK_CORE_TYPE)

        def kill_pre_solve(arbiter, space, data):
            plow, truck = arbiter.shapes  # Extract the shapes
            for s in truck.body.shapes:
                s.collision_type = DEAD_BODY_TYPE
            if truck.body.player.living:  # If he is alive
                truck.body.player.living = False  # Kill the guy that got t-boned
                self.on_death(truck.body.player)  # Call the listener, too!
            return True  # Then let his body fly across the map stupidly fast

        pb_handler.pre_solve = kill_pre_solve
        db_handler.pre_solve = kill_pre_solve

        # Between the arena and a dead player
        ad_handler = self.space.add_collision_handler(ARENA_BORDER_TYPE, DEAD_BODY_TYPE)

        def ad_pre_solve(arbiter, space, data):
            arbiter.restitution = 0.1  # Dead players shouldn't be flying around that fast...
            return True

        ad_handler.pre_solve = ad_pre_solve

        # Create borders
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        shapes = [
            pymunk.Poly(body, util.offset_box(ARENA_WIDTH / 2, -ARENA_THICKNESS / 2, ARENA_WIDTH + 2 * ARENA_THICKNESS,
                                              ARENA_THICKNESS)),
            pymunk.Poly(body, util.offset_box(ARENA_WIDTH / 2, ARENA_HEIGHT + 3 * ARENA_THICKNESS / 4,
                                              ARENA_WIDTH + 2 * ARENA_THICKNESS, ARENA_THICKNESS)),
            pymunk.Poly(body, util.offset_box(-ARENA_THICKNESS / 2, ARENA_HEIGHT / 2, ARENA_THICKNESS,
                                              ARENA_HEIGHT + 2 * ARENA_THICKNESS)),
            pymunk.Poly(body, util.offset_box(ARENA_WIDTH + 3 * ARENA_THICKNESS / 4, ARENA_HEIGHT / 2, ARENA_THICKNESS,
                                              ARENA_HEIGHT + 2 * ARENA_THICKNESS))
        ]
        for s in shapes:
            s.elasticity = 0.8
            s.collision_type = ARENA_BORDER_TYPE
        self.space.add(body, *shapes)

    def update(self, dt):
        for p in self.players:  # Push the players along in their proper directions at their proper speeds.
            force = (BOOST_FORCE if p.is_boosting() else NORMAL_FORCE) * Vec2d.unit()
            force.angle = p.rotation
            if p.living:
                p.body.velocity += force / p.body.mass
                p.body.angular_velocity = 0

        for body in self.space.bodies:  # Apply friction
            speed = body.velocity.get_length()
            if speed > 0:
                fric_dir = -body.velocity.normalized()
                fric_amount = body.mass * FRICTION
                friction_force = fric_dir * fric_amount * dt
                if speed < MIN_SPEED:
                    body.velocity = Vec2d.zero()
                else:
                    body.velocity += friction_force / body.mass
            if body.velocity.get_length() > MAX_SPEED:
                if not body.player.living:
                    max_speed = DEAD_MAX_SPEED
                elif body.player.is_boosting():
                    max_speed = BOOST_MAX_SPEED
                elif body.player.braking:
                    max_speed = BRAKE_MAX_SPEED
                else:
                    max_speed = MAX_SPEED
                body.velocity = max_speed * body.velocity.normalized()

        self.space.step(dt)  # Simulate world
        self.frames += 1

    def get_encoded(self) -> dict:
        return {
            'frames': self.frames,
            'teams': [t.get_encoded() for t in self.teams]
        }

    def get_player_by_id(self, player_id) -> (Player, None):
        for p in self.players:
            if p.id == player_id:
                return p
        return None

    def create_team(self) -> Team:
        t = Team(self, util.random_string(PLAYER_ID_LENGTH))
        self.teams.append(t)
        return t


if __name__ == '__main__':
    from pprint import pprint
    game = GameInstance()
    t1 = game.create_team()
    t1.create_player()
    t1.create_player()
    t1.create_player()
    t2 = game.create_team()
    t2.create_player()
    t2.create_player()
    t2.create_player()
    pprint(game.get_encoded())
