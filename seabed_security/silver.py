from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from functools import partial
from pprint import pprint
from collections import Counter
from typing import Any
from itertools import cycle

_debug = partial(pprint, stream=sys.stderr)


class Color(Enum):
    RED = -1
    PINK = 0
    YELLOW = 1
    GREEN = 2
    BLUE = 3


class Type(Enum):
    MONSTER = -1
    SQUID = 0
    FISH = 1
    CRAB = 2


class Light(Enum):
    OFF = 0
    ON = 1

    def __str__(self):
        return str(self.value)


class Action(Enum):
    MOVE = 'MOVE'
    WAIT = 'WAIT'

    def __str__(self):
        return self.name


class Registerable:
    register = defaultdict(dict)

    def __new__(cls, *args, **kwargs):
        id = args[0]
        cls_reg = Registerable.register[cls]
        if not (obj := cls_reg.get(id)):
            cls.register = cls_reg
            obj = super().__new__(cls)
            Registerable.register[cls][id] = obj
        return obj


def _dist(this, that):
    return abs(this.x - that.x) + abs(this.y - that.y)

@dataclass
class Creature(Registerable):
    _id: int
    _color: Color
    _type: Type

    x: int | None = None
    y: int | None = None
    vx: int | None = None
    vy: int | None = None

    scanned: bool = field(init=False, default=False)

    def __post_init__(self):
        self.pos = self.x, self.y

    @classmethod
    def from_str(cls, s):
        _id, color_n, type_n = tuple(int(c) for c in s.split())
        return cls(_id, Color(color_n), Type(type_n))

    def __hash__(self):
        return self._id

    def __str__(self):
        return f'{self._color.name}_{self._type.name}_{self._id}({self.x}, {self.y}) {self.scanned}'

    def debug_s(self):
        s = f'id: {self._id}\n'
        f'color: {self._color.value}, type: {self._type.value}\n'
        f'pos: ({self.x}, {self.y})\n'
        f'speed: ({self.vx}, {self.vy})'
        return s

    __repr__ = __str__

# in thousands
u_turn_coords = {
    2000: cycle((
        (2_000, 7_000),
        (4_000, 7_000),
        (3_000, 500),
    )),
    3999: cycle((
        (4_000, 7_000),
        (2_000, 7_000),
        (3_000, 500),
    )),
    6000: cycle((
        (6_000, 7_000),
        (8_000, 7_000),
        (7_000, 500),
    )),
    7999: cycle((
        (8_000, 7_000),
        (6_000, 7_000),
        (7_000, 500),
    )),
}

@dataclass
class Drone(Registerable):
    _id: int
    x: int | None = None
    y: int | None = None
    emergency: int | None = None
    bat: int | None = None
    light: Light | None = Light.ON
    action: Action | None = Action.WAIT

    scans: set[Creature] = field(init=False, default_factory=set)
    radar: dict[Creature, str] = field(init=False, default_factory=dict)

    dbg_msg: str = field(init=False, default=':-)')

    target: tuple[int, int] | None = field(init=False, default=None)
    tg_coords: Any = field(init=False, default=None)

    def __post_init__(self):
        self.pos = self.x, self.y

    def triangle(self):
        if not self.tg_coords:
            self.tg_coords = u_turn_coords[self.x]
        if not self.target:
            self.target = next(self.tg_coords)
        if self.pos == self.target:
            try:
                self.target = next(self.tg_coords)
            except StopIteration:
                self.target = (0, 0)
        self.dbg_msg = str(self.target)

        if len(self.scans) >= 3:
            return Action.MOVE, 5000, 0, Light.OFF

        return Action.MOVE, *self.target, Light.ON

    def chase_all(self):
        _debug('---')
        _debug(self.scans)
        _debug('---')
        if len(self.scans) > 10:
            return Action.MOVE, self.x, 0, Light.OFF

        dir_cnt = Counter(d for c, d in self.radar.items() if not c.scanned)
        _debug(dir_cnt)
        dir = dir_cnt.most_common(1)[0][0]
        
        if 'R' in dir:
            self.x += 600
        elif 'L' in dir:
            self.x -= 600
        
        if 'T' in dir:
            self.y -= 600
        elif 'B' in dir:
            self.y += 600

        self.target = self.x, self.y

        light = Light.ON if self.bat > 5 and self.y > 5000 else Light.OFF
        return Action.MOVE, *self.target, light

    strategy = triangle


creature_count = int(input())
ALL_CREATURES = {Creature.from_str(input()) for i in range(creature_count)}

MY_SCORE = 0
FOE_SCORE = 0


def get_state():
    global MY_SCORE, FOE_SCORE
    state = {}

    MY_SCORE = int(input())
    FOE_SCORE = int(input())

    my_scan_count = int(input())
    state['my_scans'] = [int(input()) for _ in range(my_scan_count)]
    foe_scan_count = int(input())
    state['foe_scans'] = [int(input()) for _ in range(foe_scan_count)]

    my_drone_count = int(input())
    state['my_drones'] = [
        dict(zip(('_id', 'x', 'y', 'emergency', 'bat'), map(int, input().split())))
        for _ in range(my_drone_count)
    ]
    foe_drone_count = int(input())
    state['foe_drones'] = [
        dict(zip(('_id', 'x', 'y', 'emergency', 'bat'), map(int, input().split())))
        for _ in range(foe_drone_count)
    ]

    drone_scan_count = int(input())
    state['drone_scans'] = [
        dict(zip(('drone_id', 'creature_id'), map(int, input().split())))
        for _ in range(drone_scan_count)
    ]

    visible_creature_count = int(input())
    state['visible_creatures'] = [
        dict(zip(('_id', 'x', 'y', 'vx', 'vy'), map(int, input().split())))
        for _ in range(visible_creature_count)
    ]

    state['radar_blip_count'] = int(input())
    state['radar_blips'] = []
    for _ in range(state['radar_blip_count']):
        inputs = input().split()
        state['radar_blips'].append(
            dict(zip(('drone_id', 'creature_id', 'direction'), [int(inputs[0]), int(inputs[1]), inputs[2]]))
        )

    return state


def update_objects_from_state(state):
    my_drones = [
        Drone(*drone_dict.values())
        for drone_dict in state['my_drones']
    ]

    foe_drones = [
        Drone(*drone_dict.values())
        for drone_dict in state['foe_drones']
    ]

    visible_creatures = []
    for creature_dict in state['visible_creatures']:
        c = Creature.register[creature_dict.pop('_id')]
        c.__dict__.update(creature_dict)
        visible_creatures.append(c)

    # scans
    for scan_dict in state['drone_scans']:
        drone = Drone.register[scan_dict['drone_id']]
        creature = Creature.register[scan_dict['creature_id']]
        drone.scans.add(creature)
        creature.scanned = True

    # radar blips
    for radar_blip_dict in state['radar_blips']:
        drone = Drone.register[radar_blip_dict['drone_id']]
        creature = Creature.register[radar_blip_dict['creature_id']]
        direction = radar_blip_dict['direction']
        drone.radar[creature] = direction

    # scanned creatures. afer submitting
    for creature_id in state['my_scans']:
        Creature.register[creature_id].scanned = True

    return my_drones, foe_drones, visible_creatures


# game loop
while True:
    state = get_state()
    my_drones, foe_drones, visible_creatures = update_objects_from_state(state)

    my_drone_scans_cnt = sum(
        scan['drone_id'] in (d._id for d in my_drones)
        for scan in state['drone_scans']
        )

    if my_drone_scans_cnt >= 10:
        # rush up
        print(Action.MOVE, 5000, 0, 1)
        print(Action.MOVE, 5000, 0, 1)
        continue

    for drone in my_drones:
        #_debug(drone.scans)
        print(*drone.strategy(), f'{drone.dbg_msg} {drone.bat}')
