import sys
import math
import numpy as np

# print(f'{first_round=}', file=sys.stderr, flush=True)

checkpoints = []

first_round = True
boost_used = False
BOOST_DIST = 5000
BOOST_ANGLE = 3

PRESTEER_DIST = 1500
PRESTEER_ANGLE = 20

SLOWDOWN_DIST = 2000  # how far should the slowdown process start
SLOWDOWN_DIST_FACTOR = 40
SLOW_ANGLE = 120

def _angle_speed(angle):
    if abs(angle) > SLOW_ANGLE:
        return 0
    else:
        return max(0, 100 - abs(angle))

def _dist_speed(distance):
    """strategies
    a) linear
        return 100 if distance > SLOWDOWN_DIST else min(100, distance // SLOWDOWN_DIST_FACTOR)
    b) modified_exp
        break_fn = lambda (dist, fac, slow): min(100, math.pow(fac, dist/(slow/2)))) 
        return break_fn()
    c) 100 or 0 based on distance
        return 0 if dist < SLOWDOWN_DIST else 100 
    
    """
    strategies = {
        'a' : lambda d, f, s_d: 100 if d > s_d else min(100, d // f),
        'b' : lambda d, f, s_d: min(100, math.pow(f, d/(s_d/2))),
        'c' : lambda d, f, s_d: min(100, math.pow(f, int(d/(s_d/2))+20)), 
    }
    # pick strategy
    break_fn = strategies['a']
    return break_fn(distance, SLOWDOWN_DIST_FACTOR, SLOWDOWN_DIST)
    
def _get_boost(target):
    global boost_used

    if first_round and not boost_used:

        if target['dist'] > BOOST_DIST and abs(target['angle']) < BOOST_ANGLE:
            boost_used = True
            return 'BOOST'
        else:
            return None

def get_speed(target):
    
    thrust = min((
        _angle_speed(next_checkpoint['angle']),
        _dist_speed(next_checkpoint['dist'])
    ))

    boost = _get_boost(target)

    return boost or int(thrust)

def get_target():

    # dont presteer in the first round
    if first_round: 
        return next_checkpoint
    
    # conditions
    is_close_to_next = next_checkpoint['dist'] < PRESTEER_DIST
    is_alligned_to_next = next_checkpoint['angle'] < PRESTEER_ANGLE

    # decision
    can_turn = is_close_to_next and is_alligned_to_next
    
    # select target
    target = future_checkpoint if can_turn else next_checkpoint

    print(f'in target {target=}', file=sys.stderr, flush=True)

    return target

def move():

    target = get_target()
    thrust = get_speed(target)

    return *target['pos'], thrust

def read_game_state():
    global first_round

    x, y, next_checkpoint_x, next_checkpoint_y, next_checkpoint_dist, next_checkpoint_angle = [int(i) for i in input().split()]
    opponent_x, opponent_y = [int(i) for i in input().split()]

    my_pos = np.array([x, y])
    his_pos = np.array([opponent_x, opponent_y])

    enemy_dist = np.linalg.norm(my_pos-his_pos)

    next_checkpoint = np.array([next_checkpoint_x, next_checkpoint_y])
    _next_checkpoint = (next_checkpoint_x, next_checkpoint_y)

    future_checkpoint = None
    future_dist = None

    if _next_checkpoint not in checkpoints:
        checkpoints.append(_next_checkpoint)
    if len(checkpoints) > 1 and _next_checkpoint == checkpoints[0]:
        first_round = False
    if first_round == False:
        index = checkpoints.index(_next_checkpoint)
        future_checkpoint = np.array(checkpoints[(index + 1) % len(checkpoints)])
        future_dist = np.linalg.norm(future_checkpoint-my_pos)

    #print(f'{checkpoints=}', file=sys.stderr, flush=True)
    #print(f'{next_checkpoint=}', file=sys.stderr, flush=True)
    #print(f'{future_checkpoint=}', file=sys.stderr, flush=True)

    def unit_vector(vector):
        return vector / np.linalg.norm(vector)

    def angle_between(v1, v2):
        # TODO: we dont know our bearing.. cant calculate proper angle
        v1_u = unit_vector(v1)
        v2_u = unit_vector(v2)
        return np.rad2deg(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))
    
    try:
        future_checkpoint_angle = angle_between(my_pos, future_checkpoint)
        #print(f'{future_checkpoint_angle=}', file=sys.stderr, flush=True)
    except:
        # we dont have future vector
        future_checkpoint_angle = None

    game_state = {
        'my_pos'          : my_pos,
        'his_pos'         : his_pos,
        'next_checkpoint' : {
            'pos'  : next_checkpoint,
            'angle': next_checkpoint_angle,
            'dist' : next_checkpoint_dist,
        },
        'future_checkpoint': {
            'pos'  : future_checkpoint,
            'angle': future_checkpoint_angle,
            'dist' : future_dist,
        },
        'first_round'     : first_round,
        'enemy_dist'      : enemy_dist,
    }

    globals().update(game_state)

    print(f'{first_round=}', file=sys.stderr, flush=True)

# game loop
while True:
    read_game_state()
    print(*move())
