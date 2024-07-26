import collections
import math
import sys
from dataclasses import dataclass
from dataclasses import field
from functools import partial

import numpy as np

log = partial(print, file=sys.stderr, flush=True)


class Params:
    SLOW_ANGLE = 30

    SLOWDOWN_DIST = 2000  # how far should the slowdown process start
    SLOWDOWN_DIST_FACTOR = 40

    BOOST_DIST = 5000
    BOOST_ANGLE = 3


def unit_vector(vector):
    return vector / np.linalg.norm(vector)


def angle_between(v1, v2):
    # TODO: we dont know our bearing.. cant calculate proper angle
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.rad2deg(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))


@dataclass(kw_only=True)
class Point:
    pos: np.ndarray = field(default_factory=lambda: np.array([0, 0]))

    def interpolate(self, dest: 'Point', percent):
        return ((1 - percent) * self.pos + percent * dest.pos).astype(int)


@dataclass
class Checkpoint(Point):
    angle: int = 0
    distance: int = 0


@dataclass
class Pod(Point):
    pass


# strategies

def steer_strategy(player: 'Player'):
    """determine future target"""
    # steering adjust
    p = 1.2
    target = player.interpolate(player.next_cp, p)
    return target


def thrust_strategy(player: 'Player'):
    """determine future thrust"""

    def by_angle(angle):
        if abs(angle) > Params.SLOW_ANGLE:
            return 5
        else:
            return max(0, 100 - abs(angle))

    def by_distance(distance):
        value = math.pow(Params.SLOWDOWN_DIST_FACTOR, distance // (Params.SLOWDOWN_DIST // 2))
        return min(100, value)

    def boost():
        if (
                not player.boost_used
                and player.next_cp.distance > Params.BOOST_DIST
                and player.next_cp.angle < Params.BOOST_ANGLE

        ):
            player.boost_used = True
            return 'BOOST'
        else:
            return None

    thrust = min(
        by_angle(player.next_cp.angle),
        by_distance(player.next_cp.distance),
    )
    boost = boost()

    return boost or int(thrust)


@dataclass
class Player(Pod):
    checkpoints: list[Checkpoint] = field(init=False, default_factory=list)
    boost_used: bool = field(init=False, default=False)

    @property
    def next_cp(self):
        return self.checkpoints[0]

    def _steer(self, strategy, checkpoints):
        return strategy(self, checkpoints)

    def _thrust(self, strategy, checkpoints):
        return strategy(self, checkpoints)

    def action(self, steer_strategy, thrust_strategy):
        steer = steer_strategy(self)
        thrust = thrust_strategy(self)
        return *steer, thrust


class Game:
    def __init__(self):
        self.first_round = True
        self.checkpoints = collections.deque()  # will be cycled later
        self.player = Player()
        self.enemy = Pod()

    def read_state(self):
        (
            x, y,
            next_checkpoint_x, next_checkpoint_y,
            next_checkpoint_dist, next_checkpoint_angle
        ) = map(int, input().split())
        opponent_x, opponent_y = map(int, input().split())

        player_pos = np.array([x, y])
        enemy_pos = np.array([opponent_x, opponent_y])
        next_cp_pos = np.array([next_checkpoint_x, next_checkpoint_y])
        next_checkpoint = Checkpoint(
            pos=next_cp_pos,
            angle=next_checkpoint_angle,
            distance=next_checkpoint_dist,
        )

        return player_pos, enemy_pos, next_checkpoint

    def _add_checkpoint(self, checkpoint):
        self.checkpoints.insert(1, checkpoint)
        self.checkpoints.rotate(-1)

    def update_state(self):
        player_pos, enemy_pos, next_checkpoint = self.read_state()

        # enemy
        self.enemy.pos = enemy_pos

        # checkpoints
        self._add_checkpoint(next_checkpoint)

        # player
        self.player.pos = player_pos
        self.player.checkpoints = self.checkpoints

    def play(self):
        while True:
            self.update_state()
            out = self.player.action(
                steer_strategy,
                thrust_strategy,
            )
            print(*out)


class MockInput:
    def __init__(self, responses):
        self.generator = self.input_generator(responses)

    def input_generator(self, responses):
        yield from responses

    def __call__(self, prompt=''):
        try:
            return next(self.generator)
        except StopIteration:
            raise SystemExit(0)


# input = MockInput(['5089 4758 11505 6078 6550 0', '4963 5750'])

g = Game()
g.play()
