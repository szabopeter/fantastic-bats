#!env python3

import sys
# import math


def dbg(msg):
    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)
    print(msg, file=sys.stderr)

# Grab Snaffles and try to throw them through the opponent's goal!
# Move towards a Snaffle and use your team id to determine where you need to throw it.


class P(object):
    def __init__(self, x, y):
        self.x, self.y = x, y

    def dist(self, other):
        return (self.x - other.x) ** 2 + (self.y - other.y) ** 2


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
ETYPES = (ETYPE_WIZARD, ETYPE_OPPONENT, ETYPE_SNAFFLE, ETYPE_BLUDGER, )

MAX_MOVE_POWER = 150
MAX_THROW_POWER = 500

TEAM_LTR = 0
TEAM_RTL = 1


class Entity(object):
    def __init__(self, entity_id, entity_type, p, v, state):
        self.entity_id, self.entity_type = entity_id, entity_type
        self.p, self.v, self.state = p, v, state
        self.markedForRemoval = False
        self.target = self.aim = None

    def closest(self, others):
        if not others:
            fake_entity = Entity(-1, ETYPE_NONE, P(MAPW//2, MAPH//2), P(0,0), 0)
            return fake_entity
        others = [{'entity': e, 'dist': e.p.dist(self.p)} for e in others]
        by_dist = sorted(others, key=lambda pair: pair['dist'])
        return by_dist[0]['entity']

    def __str__(self):
        return "%s%d@%d,%d"%(self.entity_type, self.entity_id, self.p.x, self.p.y)

class GameState(object):
    def __init__(self, my_team_id):
        self.my_team_id = my_team_id
        self.entities = dict([(etype, {}) for etype in ETYPES])
        self.wizards = {}
        self.snaffles = {}
        self.mana = 0
        # IMPROVEMENT: count opponent mana (complex)

    def update_entity(self, entity):
        etype, eid = entity.entity_type, entity.entity_id
        assert etype in self.entities

        # if not entity.entity_id in self.entities[entity.entity_type]:
        self.entities[etype][eid] = entity
        entity.markedForRemoval = False

    def get_all(self, entity_type):
        return list(self.entities[entity_type].values())

    def set_targets(self):
        wizards = self.get_all(ETYPE_WIZARD)
        targets = self.get_all(ETYPE_SNAFFLE)
        for wiz in wizards:
            if wiz.state == STATE_WITH_SNAFFLE:
                wiz.target = None
                wiz.aim = self.get_goal()
            else:
                wiz.target = wiz.closest(targets)
                wiz.aim = None

        wiz1, wiz2 = wizards
        if wiz1.target == wiz2.target:
            if len(targets) > 1 and wiz1.target is not None:
                if not wiz1.target in targets:
                    dbg("%s not in %s"%(wiz1.target, [str(x) for x in targets],))
                targets.remove(wiz1.target)
                alttarg1 = wiz1.closest(targets)
                alttarg2 = wiz2.closest(targets)
                altdist1 = wiz1.p.dist(alttarg1.p)
                altdist2 = wiz2.p.dist(alttarg2.p)
                if altdist1 < altdist2:
                    wiz1.target = alttarg1
                else:
                    wiz2.target = alttarg1

    def get_goal(self):
        return POLE_RIGHT if self.my_team_id == TEAM_LTR else POLE_LEFT

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
        self.mana += 1


class GameLogic(object):
    def __init__(self):
        pass

    @staticmethod
    def execute():
        my_team_id = int(input())  # if 0 you need to score on the right of the map, if 1 you need to score on the left
        gamestate = GameState(my_team_id)
        goal = gamestate.get_goal()

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
                if wiz.aim:
                    print("THROW %d %d 500" % (wiz.aim.x, wiz.aim.y,))
                else:
                    print("MOVE %d %d 150" % (wiz.target.p.x, wiz.target.p.y,))


if __name__ == "__main__":
    GameLogic().execute()

