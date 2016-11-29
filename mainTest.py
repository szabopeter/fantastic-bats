import unittest

from main import *


def id_generator():
    nextid = 1
    while True:
        yield nextid
        nextid += 1

idgenerator = id_generator()


def next_id():
    return idgenerator.__next__()


def mk_default_entity(**kwargs):
    e = Entity(next_id(), ETYPE_SNAFFLE, P(0, 0), P(0, 0), 0)
    for k, v in kwargs.items():
        if k == 'p':
            e.p = v
        elif k == 'entity_type':
            e.entity_type = v
        else:
            raise AttributeError("Unknown attribute: " + k)
    return e

def mk_default_wizards():
    wiz1 = mk_default_entity(entity_type=ETYPE_WIZARD, p=P(4000, 2000))
    wiz2 = mk_default_entity(entity_type=ETYPE_WIZARD, p=P(4000, 3000))
    op1 = mk_default_entity(entity_type=ETYPE_OPPONENT, p=P(12000, 2000))
    op2 = mk_default_entity(entity_type=ETYPE_OPPONENT, p=P(12000, 3000))
    return wiz1, wiz2, op1, op2


class EntityTestCase(unittest.TestCase):
    def testClosest(self):
        o = mk_default_entity(p=P(100,50))
        e1 = mk_default_entity(p=P(130, 150))
        e2 = mk_default_entity(p=P(200, 25))
        closest = o.closest((e1, e2,))
        self.assertEqual(e2, closest)


class GameStateTestCase(unittest.TestCase):
    def testRemovalOnUpdate(self):
        state = GameState(TEAM_LTR)
        updated_entity = mk_default_entity()
        abandoned_entity = mk_default_entity()
        state.update((updated_entity, abandoned_entity,))
        self.assertEqual(2, len(state.entities[ETYPE_SNAFFLE]))
        state.update((updated_entity,))
        self.assertEqual(1, len(state.entities[ETYPE_SNAFFLE]))
        self.assertEqual(updated_entity, state.entities[ETYPE_SNAFFLE][updated_entity.entity_id])

    def testChosingLastTarget(self):
        state = GameState(TEAM_LTR)
        wiz1, wiz2, _, _ = mk_default_wizards()
        snaffle = mk_default_entity(p=P(6000, 2000))
        state.update((wiz1, wiz2, snaffle))
        state.set_targets()
        self.assertEqual(snaffle, wiz1.target)
        self.assertEqual(snaffle, wiz2.target)

    def testChosingNoTarget(self):
        state = GameState(TEAM_LTR)
        wiz1, wiz2, _, _ = mk_default_wizards()
        state.update((wiz1, wiz2, ))
        state.set_targets()
        self.assertEqual(ETYPE_NONE, wiz1.target.entity_type)
        self.assertEqual(ETYPE_NONE, wiz2.target.entity_type)

if __name__ == '__main__':
    unittest.main()
