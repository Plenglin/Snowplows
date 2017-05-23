"""Code that runs the actual game itself. It should be as independent from the graphics and client-server interface 
as possible. """
import math
import random
import threading
import time

import pymunk
from pymunk import Vec2d

import util
from constants import *


class Player:
    """
    A single player, dead or alive
    """

    def __init__(self, player_id, room, body, living=True):
        self.id = player_id
        self.room = room
        self.body = body
        self.living = living

        self.began_boost = 0
        self.braking = False

    def get_pos(self):
        return self.body.position

    def is_boosting(self):
        return self.began_boost + BOOST_DURATION > time.time()

    def get_boost_level(self):
        if self.is_boosting():
            return 1 - min(1, (time.time() - self.began_boost) / BOOST_DURATION)
        else:
            return min(1, (time.time() - (self.began_boost + BOOST_DURATION)) / BOOST_COOLDOWN)

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
    def __init__(self):
        self.players = []

    def __iter__(self):
        return self.players


class GameInstance:
    """
    A single instance of the game. Only handles game updates and stuff. Nothing else. After all, we don't want a god
    object. Handle communication somewhere else.
    """

    def __init__(self):
        self.teams = []
        self.space = pymunk.Space()
        self.room_name = util.random_string(ROOM_NAME_LENGTH)

        # Listeners
        self.on_death = lambda p: None

    @property
    def players(self):
        for t in self.teams:
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

    def get_encoded_positions(self):
        return [
            {
                'id': player.id,
                'x': player.get_pos().x,
                'y': player.get_pos().y,
                'living': player.living,
                'direction': player.rotation,
                'isBoosting': player.is_boosting(),
                'boostLevel': player.get_boost_level(),
            } for player in self.players
        ]

    def get_player_by_id(self, player_id):
        for p in self.players:
            if p.id == player_id:
                return p
        return None

    def create_player(self, team, player_id):

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

        # Add the player to the things
        self.space.add(body, front_physical, back_physical)
        player = Player(player_id, self, body)
        self.players.append(player)
        body.player = player

    def remove_player(self, player_id):
        for p in self.players:
            if p.id == player_id:
                self.space.remove(p.body, *p.body.shapes)
                self.players.remove(p)
                return


class RoomThread(threading.Thread):
    def __init__(self, room):
        super().__init__()
        self.room = room

    def run(self):
        self.room.init()
        while True:
            self.room.update(UPDATE_PERIOD)
            time.sleep(UPDATE_PERIOD)
