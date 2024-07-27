import collections
import math
import sys
from dataclasses import dataclass
from dataclasses import field
from functools import cached_property
from functools import partial

import numpy as np

log = partial(print, file=sys.stderr, flush=True)


class Params:
    SLOW_ANGLE = 90

    SLOWDOWN_DIST = 1000  # how far should the slowdown process start
    SLOWDOWN_DIST_FACTOR = 20

    BOOST_DIST = 2000
    BOOST_ANGLE = 3


# ========== helper functions ==========

def unit_vector(vector):
    return vector / np.linalg.norm(vector)


def angle_between(v1, v2):
    # TODO: we dont know our bearing.. cant calculate proper angle
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.rad2deg(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))


# ========== base classes ==========

class State:
    def action(self, context):
        raise NotImplementedError("Subclasses must implement this method")

    def next_state(self, context):
        raise NotImplementedError("Subclasses must implement this method")


@dataclass(kw_only=True)
class Point:
    pos: np.ndarray = field(default_factory=lambda: np.array([0, 0]))

    def interpolate_percent(self, dest: 'Point', percent):
        return ((1 - percent) * self.pos + percent * dest.pos).astype(int)

    def interpolate_units(self, dest: 'Point', amt: int):
        direction = dest.pos - self.pos
        direction_normalized = direction / np.linalg.norm(direction)
        X = self.pos + direction_normalized * amt
        return X.astype(int)


# ========== reusable strategies ==========

def steer_strategy(player: 'Player'):
    """determine future target"""
    # steering adjust
    p = 1.2
    target = player.interpolate(player.next_cp, p)
    return target


def steer_strategy(player: 'Player'):
    """determine future target"""
    return player.next_cp.aimpoint


def thrust_strategy(player: 'Player'):
    """determine future thrust"""

    def by_angle(angle):
        if abs(angle) > Params.SLOW_ANGLE:
            return 30
        else:
            return 100

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


# ========== state ==========


class FirstRound(State):
    def action(self, context):
        steer = steer_strategy(context)
        thrust = thrust_strategy(context)
        print(*steer, thrust)

    def next_state(self, context):
        # TODO: add proper transition after first round
        return Race()


class Race(State):
    def action(self, context):
        steer = steer_strategy(context)
        thrust = thrust_strategy(context)
        print(*steer, thrust)

    def next_state(self, context):
        return self


class StateMachine:
    def __init__(self, initial_state):
        self.context = None
        self.state = initial_state

    def set_context(self, context):
        self.context = context

    def action(self):
        if self.state is None:
            raise SystemExit("State machine is empty")

        self.state.action(self.context)
        self.state = self.state.next_state(self.context)


# ========== game entities ==========

ARENA_CENTER = Point(pos=np.array([8000, 4500]))


@dataclass
class Checkpoint(Point):
    angle: int = 0
    distance: int = 0
    radius: int = 600

    @cached_property
    def aimpoint(self):
        return self.interpolate_units(ARENA_CENTER, self.radius)


@dataclass
class Pod(Point):
    pass


@dataclass
class Player(Pod):
    initial_state: State
    state_machine: StateMachine = field(init=False)
    checkpoints: list[Checkpoint] = field(init=False, default_factory=list)
    boost_used: bool = field(init=False, default=False)

    def __post_init__(self):
        self.state_machine = StateMachine(self.initial_state)
        self.state_machine.set_context(self)

    @property
    def next_cp(self):
        return self.checkpoints[0]


class Game:
    def __init__(self):
        self.first_round = True
        self.checkpoints = collections.deque()  # will be cycled later

        # prepare player
        self.player = Player(initial_state=FirstRound())
        self.enemy = Pod()

    @staticmethod
    def read_state():
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
            self.player.state_machine.action()


class MockInput:
    def __init__(self, responses):
        self.responses = iter(responses)

    def __call__(self, prompt=''):
        return next(self.responses)


# input = MockInput(['5089 4758 11505 6078 6550 0', '4963 5750'])

g = Game()
g.play()
