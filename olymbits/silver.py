import sys
from collections import Counter
from dataclasses import dataclass
from dataclasses import field
from functools import partial
from operator import itemgetter

log = partial(print, file=sys.stderr, flush=True)

RESET_STR = 'GAME_OVER'
POSSIBLE_MOVES = 'UP', 'DOWN', 'LEFT', 'RIGHT'

player_idx = int(input())
nb_games = int(input())


@dataclass
class ArcadeGame:
    gpu: str
    reg_0: int
    reg_1: int
    reg_2: int
    reg_3: int
    reg_4: int
    reg_5: int
    reg_6: int

    reg: list[int] = field(init=False, default_factory=list)

    move_abbrev: dict[str, str] = field(init=False, default_factory=lambda: {
        'U': 'UP',
        'D': 'DOWN',
        'L': 'LEFT',
        'R': 'RIGHT',
    })

    medals: list[int] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.reg = [
            self.reg_0,
            self.reg_1,
            self.reg_2,
            self.reg_3,
            self.reg_4,
            self.reg_5,
            self.reg_6,
        ]

    @classmethod
    def from_input(cls):
        gpu, *regs = input().split()
        return cls(gpu, *map(int, regs))

    def decide_weight(self):
        gold, silver, bronze = self.medals

        if not (gold or silver):
            return 30
        return 1

    def next_move(self):
        raise NotImplementedError


class Hurdles(ArcadeGame):
    moves = {
        '#'  : 'UP',
        '...': 'RIGHT',
        '..' : 'DOWN',
        '.'  : 'LEFT',
    }

    @property
    def look_ahead(self):
        """return str of next 3 fields"""
        pp = self.reg[player_idx] + 1  # player pos
        look = self.gpu[pp: pp + 3].rjust(3, '.')
        return look

    def next_move(self):
        move = next(
            (
                v
                for k, v in self.moves.items()
                if self.look_ahead.startswith(k)
            ),
            'UP'  # default
        )
        return move


class Archery(ArcadeGame):
    moves = {
        'UP'   : (0, -1),
        'DOWN' : (0, 1),
        'LEFT' : (-1, 0),
        'RIGHT': (1, 0),
    }

    def new_positions(self) -> dict[str, tuple[int]]:
        coord_pos = itemgetter(player_idx * 2, player_idx * 2 + 1)
        x, y = coord_pos(self.reg)
        try:
            v = int(self.gpu[0])
        except ValueError:
            v = 0
        new_pos = {
            move: abs(x + dx * v) + abs(y + dy * v)
            for move, (dx, dy) in self.moves.items()
        }
        return new_pos

    def next_move(self) -> str:
        positions = self.new_positions()
        best_first = sorted(positions.items(), key=itemgetter(1))
        best_move = best_first[0][0]
        return best_move


class Roller(ArcadeGame):

    def next_move(self):
        # go for zero risk
        # TODO: improve this
        letter = self.gpu[2]
        move = self.move_abbrev.get(letter, 'UP')
        return move


class Diving(ArcadeGame):

    def next_move(self):
        # TODO: improve this
        letter = self.gpu[0]
        move = self.move_abbrev.get(letter, 'UP')
        return move

    def decide_weight(self):
        sw = super().decide_weight()
        return max(sw, 2)


def parse_score():
    scores = [
        list(map(int, input().split()))
        for _ in range(3)
    ]
    my_score = scores[player_idx]
    return my_score


while True:

    my_score = parse_score()
    total_score = my_score.pop(0)

    weighted_moves = Counter(dict.fromkeys(POSSIBLE_MOVES, 0))

    for i, game in enumerate((Hurdles, Archery, Roller, Diving)):
        # create games and attach medals
        g = game.from_input()
        g.medals = my_score[i * 3:(i + 1) * 3]

        # decide weight and move
        weight = g.decide_weight()
        selected_move = g.next_move()

        # add to decision pool
        weighted_moves[selected_move] += weight
        # log decision
        log(
            f'{g.__class__.__name__:<8}'
            f'| medals: {g.medals}'
            f'| move: {selected_move:<5}'
            f'| weight: {weight}'
        )

    best_move = weighted_moves.most_common()[0][0]

    print(best_move)
