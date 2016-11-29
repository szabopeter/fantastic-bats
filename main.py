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
ETYPE_WIZARD = "WIZARD"
ETYPE_OPPONENT = "OPPONENT_WIZARD"
ETYPE_SNAFFLE = "SNAFFLE"
ETYPE_BLUDGER = "BLUDGER"

MAX_MOVE_POWER = 150
MAX_THROW_POWER = 500

TEAM_LTR = 0
TEAM_RTL = 1


def mkp(pt, team_id):
    if team_id == TEAM_LTR:
        return pt
    else:
        return P(MAPW - 1 - pt.x, pt.y)


class Entity(object):
    def __init__(self, entity_id, entity_type, p, v, state):
        self.entity_id, self.entity_type = entity_id, entity_type
        self.p, self.v, self.state = p, v, state
        self.markedForRemoval = False


class GameState(object):
    def __init__(self, my_team_id):
        self.my_team_id = my_team_id
        self.entities = {}

    def update_entity(self, entity):
        if entity.entity_type not in self.entities:
            self.entities[entity.entity_type] = {}

        # if not entity.entity_id in self.entities[entity.entity_type]:
        self.entities[entity.entity_type][entity.entity_id] = entity
        entity.markedForRemoval = False

    def get_my_wizards(self):
        return list(self.entities[ETYPE_WIZARD].values())

    def get_target_for(self, wizard):
        snaffles = list(self.entities[ETYPE_SNAFFLE].values())

        if not snaffles:
            return P(8000, 3750)

        if len(snaffles) == 1:
            return snaffles[0].p

        return snaffles[wizard.entity_id % TEAM_SIZE].p

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


class GameLogic(object):
    def __init__(self):
        pass

    @staticmethod
    def execute():
        my_team_id = int(input())  # if 0 you need to score on the right of the map, if 1 you need to score on the left
        gamestate = GameState(my_team_id)

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
                entity = Entity(entity_id, entity_type, mkp(P(x, y), my_team_id), P(vx, vy), state)
                to_update.append(entity)

            gamestate.update(to_update)

            for wiz in gamestate.get_my_wizards():
                # Edit this line to indicate the action for each wizard (0 <= thrust <= 150, 0 <= power <= 500)
                # i.e.: "MOVE x y thrust" or "THROW x y power"
                goal = gamestate.get_goal()
                if wiz.state == STATE_WITH_SNAFFLE:
                    print("THROW %d %d 500" % (goal.x, goal.y,))
                else:
                    # TODO: move to closest snaffle
                    target = mkp(gamestate.get_target_for(wiz), my_team_id)
                    print("MOVE %d %d 100" % (target.x, target.y,))


if __name__ == "__main__":
    GameLogic().execute()

