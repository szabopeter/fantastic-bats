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


def mk_default_entity():
    e = Entity(next_id(), ETYPE_SNAFFLE, P(0, 0), P(0, 0), 0)
    return e


class GameStateTestCase(unittest.TestCase):
    def testRemovalOnUpdate(self):
        state = GameState(0)
        updated_entity = mk_default_entity()
        abandoned_entity = mk_default_entity()
        state.update((updated_entity, abandoned_entity,))
        self.assertEqual(2, len(state.entities[ETYPE_SNAFFLE]))
        state.update((updated_entity,))
        self.assertEqual(1, len(state.entities[ETYPE_SNAFFLE]))
        self.assertEqual(updated_entity, state.entities[ETYPE_SNAFFLE][updated_entity.entity_id])


if __name__ == '__main__':
    unittest.main()
