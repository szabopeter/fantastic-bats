#!env python3

import sys
import itertools
import math


def dbg(msg):
    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)
    print(msg, file=sys.stderr)

# Grab Snaffles and try to throw them through the opponent's goal!
# Move towards a Snaffle and use your team id to determine where you need to throw it.

class RunConf(object):
    def __init__(self, throw_dist=1200, throw_directions=None, bludger_close=900):
        self.APPROX_THROW_DIST = throw_dist
        self.GOAL_LINE_PROXIMITY = throw_dist
        if not throw_directions:
            throw_directions = generate_directional_coordinates(0, 360, 10)
        self.throw_directions = throw_directions
        self.BLUDGER_CLOSE = bludger_close

        self.SCOREMAX_DIST = 20000 * 20000
        # POS16 (THROWDIST = 600)
        # SNAFFLE_AIM_WEIGHT_GOALDIST = 1000
        # SNAFFLE_AIM_WEIGHT_OBSTACLEDIST = 1

        # POS38 (THROWDIST = 600)
        # POS19 (THROWDIST = 900)
        # POS44 (THROWDIST = 1100)
        # POS8 (THROWDIST = 1200)
        # POS61 (THROWDIST = 1500)
        self.SNAFFLE_AIM_WEIGHT_GOALDIST = 100
        self.SNAFFLE_AIM_WEIGHT_OBSTACLEDIST = 1
        self.WILLING_TO_SPEND_MANA = 25
        self.TOO_FAR_TO_ACT = 6000

class P(object):
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __repr__(self):
        return "P(%d,%d)" % (self.x, self.y,)

    def __eq__(self, other):
        return (self.x, self.y,) == (other.x, other.y,)

    def __hash__(self):
        return self.x

    def minus(self, other):
        return P(self.x - other.x, self.y - other.y)

    def plus(self, other):
        return P(self.x + other.x, self.y + other.y)

    def times(self, factor):
        return P(self.x * factor, self.y * factor)

    def dist(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def dists(self, others):
        return [{'e': other, 'dist': self.dist(other)} for other in others]

class Cmd(object):
    def __str__(self):
        raise Exception("Uninitialized command!")

class CmdMove(Cmd):
    def __init__(self, target, thrust):
        self.target = target
        self.thrust = thrust

    def __str__(self):
        return "MOVE %d %d %d" % (self.target.x, self.target.y, self.thrust,)

class CmdThrow(Cmd):
    def __init__(self, aim, thrust):
        self.aim = aim
        self.thrust = thrust

    def __str__(self):
        return "THROW %d %d %d" % (self.aim.x, self.aim.y, self.thrust,)

class CmdSpell(Cmd):
    def __init__(self, word, target):
        self.target = target
        self.word = word

    def __str__(self):
        return "%s %d" % (self.word, self.target.entity_id,)

class CmdObliviate(CmdSpell):
    mana = 5
    duration = 3

    def __init__(self, target):
        CmdSpell.__init__(self, "OBLIVIATE", target)

class CmdPetrificus(CmdSpell):
    mana = 10
    duration = 1

    def __init__(self, target):
        CmdSpell.__init__(self, "PETRIFICUS", target)

class CmdAccio(CmdSpell):
    mana = 20
    duration = 6

    def __init__(self, target):
        CmdSpell.__init__(self, "ACCIO", target)

class CmdFlipendo(CmdSpell):
    mana = 20
    duration = 3

    def __init__(self, target):
        CmdSpell.__init__(self, "FLIPENDO", target)

MAPW = 16001
MAPH = 7501
POLE_RADIUS = 300
POLE_LEFT = P(0, 3750)
POLE_RIGHT = P(16000, 3750)

STATE_WITH_SNAFFLE = 1
SNAFFLE_RADIUS = 150
TEAM_SIZE = 2
WIZARD_RADIUS = 400

# entity_type: "WIZARD", "OPPONENT_WIZARD" or "SNAFFLE" (or "BLUDGER" after first league)
ETYPE_NONE = "NONE"
ETYPE_WIZARD = "WIZARD"
ETYPE_OPPONENT = "OPPONENT_WIZARD"
ETYPE_SNAFFLE = "SNAFFLE"
ETYPE_BLUDGER = "BLUDGER"
ETYPES = (ETYPE_WIZARD, ETYPE_OPPONENT, ETYPE_SNAFFLE, ETYPE_BLUDGER,)

MAX_MOVE_POWER = 150
MAX_THROW_POWER = 500

TEAM_LTR = 0
TEAM_RTL = 1

CMD_CLUELESS = CmdMove(P(MAPW // 2, MAPH // 2), 42)

def generate_directional_coordinates(startdeg, enddeg, step):
    directions = []
    for dg in range(startdeg, enddeg, step):
        rad = math.pi * dg / 180
        y = math.sin(rad)
        x = math.cos(rad)
        directions.append(P(x, y))
    return directions

THROW_DIRECTIONS = generate_directional_coordinates(0, 360, 10)

class Entity(object):
    def __init__(self, entity_id, entity_type, p, v, state):
        self.entity_id, self.entity_type = entity_id, entity_type
        self.p, self.v, self.state = p, v, state
        self.markedForRemoval = False
        self.casting = 0

    def closest(self, others):
        if not others:
            fake_entity = Entity(-1, ETYPE_NONE, P(MAPW // 2, MAPH // 2), P(0, 0), 0)
            return fake_entity
        others = [{'entity': e, 'dist': e.p.dist(self.p)} for e in others]
        closest = min(others, key=lambda pair: pair['dist'])
        return closest['entity']

    def __str__(self):
        return "%s%d@%d,%d" % (self.entity_type, self.entity_id, self.p.x, self.p.y)

class GameState(object):
    def __init__(self, my_team_id, config=None, throw_directions=generate_directional_coordinates(0, 360, 10)):
        if not config:
            config = RunConf()
        self.config = config
        self.my_team_id = my_team_id
        self.entities = dict([(etype, {}) for etype in ETYPES])
        self.wizards = {}
        self.snaffles = {}
        self.mana = 0
        self.throw_directions = config.throw_directions
        # IMPROVEMENT: count opponent mana (complex)

    def update_entity(self, entity):
        etype, eid = entity.entity_type, entity.entity_id
        assert etype in self.entities

        # if not entity.entity_id in self.entities[entity.entity_type]:
        self.entities[etype][eid] = entity
        entity.markedForRemoval = False
        entity.casting -= 1
        entity.cmd = None

    def get_all(self, *entity_types):
        entities = []
        for l in [list(self.entities[etype].values()) for etype in entity_types]:
            entities.extend(l)
        return entities

    def guess_throw(self, pt, d):
        return pt.plus(d.times(self.config.APPROX_THROW_DIST))

    def dist_score(self, p1, p2):
        return self.config.SCOREMAX_DIST / (1 + p1.dist(p2)) ** 2

    def score_for_snafflepos(self, pt, obst):
        goal_dist = self.dist_score(pt, self.get_goal())
        obst_dist = sum([self.dist_score(pt, obs.p) for obs in obst]) / len(obst) if obst else 0
        score = self.config.SNAFFLE_AIM_WEIGHT_GOALDIST * goal_dist \
                - self.config.SNAFFLE_AIM_WEIGHT_OBSTACLEDIST * obst_dist

        if self.crosses_my_goalline(pt.x):
            score = -100

        return score

    def aim_from(self, pt):
        if pt.dist(self.get_goal()) < self.config.GOAL_LINE_PROXIMITY:
            return self.get_goal()

        obst = self.get_all(ETYPE_OPPONENT, ETYPE_BLUDGER)
        opts = [self.guess_throw(pt, d) for d in self.throw_directions]
        opts = [{'goal': opt, 'score': self.score_for_snafflepos(opt, obst)} for opt in opts]
        best_opt = max(opts, key=lambda x: x['score'])
        return best_opt['goal']

    def set_targets(self):
        wizards = self.get_all(ETYPE_WIZARD)
        targets = [target.p for target in self.get_all(ETYPE_SNAFFLE)]
        bludgers = self.get_all(ETYPE_BLUDGER)

        casting_this_turn = False
        dists = {}
        for wiz in wizards[:]:
            danger = self.bludger_close(wiz, bludgers)
            dbg("DANGER: " + str(danger))
            if wiz.state == STATE_WITH_SNAFFLE:
                aim = self.aim_from(wiz.p)
                aim = aim.minus(wiz.v)
                wiz.cmd = CmdThrow(aim, MAX_THROW_POWER)
                wizards.remove(wiz)
            elif self.mana > CmdObliviate.mana and wiz.casting < 1 and danger:
                wiz.cmd = CmdObliviate(danger)
                wiz.casting = wiz.cmd.duration
                wizards.remove(wiz)
            else:
                dists[wiz] = {}
                for target in targets:
                    dists[wiz][target] = wiz.p.dist(target)
                if not casting_this_turn \
                        and wiz.casting < 1 \
                        and min(dists[wiz].values()) >= self.config.TOO_FAR_TO_ACT \
                        and self.mana > self.config.WILLING_TO_SPEND_MANA:
                    wiz.cmd = self.choose_spell(wiz)
                    wiz.casting = wiz.cmd.duration
                    wizards.remove(wiz)
                    casting_this_turn = True

        if not targets:
            return

        random_target = targets[0]

        while len(targets) < len(wizards):
            targets.append(random_target)

        permutations = []
        for p in itertools.permutations(targets, len(wizards)):
            pd = 0
            for i, wiz in enumerate(wizards):
                target = p[i]
                if wiz not in dists or target not in dists[wiz]:
                    dists[wiz][target] = target.dist(wiz.p)
                pd += dists[wiz][target]
            permutations.append({'d': pd, 'p': p})

        permutations.sort(key=lambda pair: pair['d'])
        best = permutations[0]['p']
        for i, wiz in enumerate(wizards):
            wiz.cmd = CmdMove(best[i], MAX_MOVE_POWER)

    def bludger_close(self, wizard, bludgers):
        for b in bludgers:
            if b.p.plus(b.v).dist(wizard.p) < self.config.BLUDGER_CLOSE:
                return b
        return None

    def choose_spell(self, wizard):
        goal = self.get_goal()
        closest = wizard.closest(self.get_all(ETYPE_SNAFFLE))
        # snaffles = [ {'s': s, 'd': wizard.p.dist(s.pt)} for s in self.get_all(ETYPE_SNAFFLE) ]
        # closest = min(snaffles, key=lambda pair:pair['d'])['s']
        # farthest = max(snaffles, key=lambda pair:pair['d'])['s']
        if goal.x > wizard.p.x and closest.p.x > wizard.p.x:
            return CmdFlipendo(closest)
        if goal.x < wizard.p.x and closest.p.x < wizard.p.x:
            return CmdFlipendo(closest)
        if goal.x > wizard.p.x and closest.p.x < wizard.p.x:
            return CmdAccio(closest)
        if goal.x < wizard.p.x and closest.p.x > wizard.p.x:
            return CmdAccio(closest)

        ops = self.get_all(ETYPE_OPPONENT)
        return CmdPetrificus(ops[0])

    def get_goal(self):
        return POLE_RIGHT if self.my_team_id == TEAM_LTR else POLE_LEFT

    def crosses_my_goalline(self, x):
        if self.my_team_id == TEAM_LTR:
            return POLE_RIGHT.x - x < 50
        return x < 50

    def mark_for_removal(self):
        for entity_type in self.entities.keys():
            for entity in self.entities[entity_type].values():
                entity.markedForRemoval = True

    def remove_marked_entities(self):
        for entity_type in self.entities.keys():
            to_remove = []
            for entity in self.entities[entity_type].values():
                if entity.markedForRemoval:
                    to_remove.append(entity.entity_id)
            for eid in to_remove:
                del self.entities[entity_type][eid]

    def update(self, entities):
        self.mark_for_removal()
        for entity in entities:
            self.update_entity(entity)
        self.remove_marked_entities()
        for e in self.get_all(ETYPE_WIZARD, ETYPE_SNAFFLE, ETYPE_OPPONENT, ETYPE_BLUDGER):
            e.p = e.p.plus(e.v)
        self.mana += 1

    def draw_mana(self, mana):
        self.mana -= mana

class GameLogic(object):
    def __init__(self):
        pass

    @staticmethod
    def execute():
        my_team_id = int(input())  # if 0 you need to score on the right of the map, if 1 you need to score on the left
        gamestate = GameState(my_team_id, config=RunConf())

        # game loop
        while True:
            entities = int(input())  # number of entities still in game
            to_update = []
            for i in range(entities):
                # entity_id: entity identifier
                # entity_type: "WIZARD", "OPPONENT_WIZARD" or "SNAFFLE" (or "BLUDGER" after first league)
                # x: position
                # y: position
                # vx: velocity
                # vy: velocity
                # state: 1 if the wizard is holding a Snaffle, 0 otherwise
                entity_id, entity_type, x, y, vx, vy, state = input().split()
                entity_id = int(entity_id)
                x = int(x)
                y = int(y)
                vx = int(vx)
                vy = int(vy)
                state = int(state)
                entity = Entity(entity_id, entity_type, P(x, y), P(vx, vy), state)
                to_update.append(entity)

            gamestate.update(to_update)
            gamestate.set_targets()

            for wiz in gamestate.get_all(ETYPE_WIZARD):
                # Edit this line to indicate the action for each wizard (0 <= thrust <= 150, 0 <= power <= 500)
                # i.e.: "MOVE x y thrust" or "THROW x y power"
                if wiz.cmd:
                    print(str(wiz.cmd))
                    if isinstance(wiz.cmd, CmdSpell):
                        gamestate.draw_mana(wiz.cmd.mana)
                else:
                    print(CMD_CLUELESS)
                    dbg("Nobody expects the spanish inquisition.")

if __name__ == "__main__":
    GameLogic().execute()
