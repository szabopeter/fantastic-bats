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
        elif k == 'status':
            e.status = v
        else:
            raise AttributeError("Unknown attribute: " + k)
    return e


def mk_default_wizards():
    wiz1 = mk_default_entity(entity_type=ETYPE_WIZARD, p=P(4000, 2000))
    wiz2 = mk_default_entity(entity_type=ETYPE_WIZARD, p=P(4000, 3000))
    op1 = mk_default_entity(entity_type=ETYPE_OPPONENT, p=P(12000, 2000))
    op2 = mk_default_entity(entity_type=ETYPE_OPPONENT, p=P(12000, 3000))
    return wiz1, wiz2, op1, op2


RIGHT, UP, LEFT, DOWN = generate_directional_coordinates(0, 360, 90)
simplified_throwing_directions = (UP, DOWN, LEFT, RIGHT)

class GeomTestCase(unittest.TestCase):
    def testMinus(self):
        a = P(300, 100)
        b = P(250, 110)
        self.assertEqual(P(-50, 10), b.minus(a))

    def testPlus(self):
        a = P(300, 100)
        v = P(-10, 30)
        self.assertEqual(P(290, 130), a.plus(v))

    def testTimes(self):
        v = P(3, -4)
        self.assertEqual(P(15, -20), v.times(5))

class EntityTestCase(unittest.TestCase):
    def testClosest(self):
        o = mk_default_entity(p=P(100,50))
        e1 = mk_default_entity(p=P(130, 150))
        e2 = mk_default_entity(p=P(200, 25))
        closest = o.closest((e1, e2,))
        self.assertEqual(e2, closest)


class GameStateTestCase(unittest.TestCase):
    def testGetAll(self):
        state = GameState(TEAM_LTR)
        w1, w2, o1, o2 = mk_default_wizards()
        state.update((w1, w2, o1, o2, mk_default_entity(), ))
        self.assertSetEqual(set((w1, w2,)), set(state.get_all(ETYPE_WIZARD)))
        self.assertSetEqual(set((o1, o2,)), set(state.get_all(ETYPE_OPPONENT)))
        self.assertSetEqual(set((w1, w2, o1, o2,)), set(state.get_all(ETYPE_WIZARD, ETYPE_OPPONENT)))

    def testRemovalOnUpdate(self):
        state = GameState(TEAM_LTR)
        updated_entity = mk_default_entity()
        abandoned_entity = mk_default_entity()
        state.update((updated_entity, abandoned_entity,))
        self.assertEqual(2, len(state.entities[ETYPE_SNAFFLE]))
        state.update((updated_entity,))
        self.assertEqual(1, len(state.entities[ETYPE_SNAFFLE]))
        self.assertEqual(updated_entity, state.entities[ETYPE_SNAFFLE][updated_entity.entity_id])

    def testChoosingLastTarget(self):
        state = GameState(TEAM_LTR)
        wiz1, wiz2, _, _ = mk_default_wizards()
        snaffle = mk_default_entity(p=P(6000, 2000))
        state.update((wiz1, wiz2, snaffle))
        state.set_targets()
        self.assertEqual(snaffle.p, wiz1.cmd.target)
        self.assertEqual(snaffle.p, wiz2.cmd.target)

    def testChoosingNoTarget(self):
        state = GameState(TEAM_LTR)
        wiz1, wiz2, _, _ = mk_default_wizards()
        state.update((wiz1, wiz2, ))
        state.set_targets()
        self.assertIsNone(wiz1.cmd)
        self.assertIsNone(wiz2.cmd)

    def testChoosingDifferentTargets(self):
        """
        W1---d1+500---snaf1
        |d1
        halfway
        |d2
        W2
        Expectation: W1->snaf1, W2->halfway
        """
        state = GameState(TEAM_LTR)
        wiz1, wiz2, _, _ = mk_default_wizards()
        halfway = mk_default_entity(p=P(4000, (2000+3000)/2))
        snaf1 = mk_default_entity(p=P(4000+800, 2000))
        state.update((wiz1, wiz2, snaf1, halfway,))
        state.set_targets()
        self.assertIsInstance(wiz1.cmd, CmdMove)
        self.assertIsInstance(wiz2.cmd, CmdMove)
        self.assertEqual(snaf1.p, wiz1.cmd.target, "%s != %s"%(snaf1, wiz1.cmd, ))
        self.assertEqual(halfway.p, wiz2.cmd.target, "%s != %s"%(halfway, wiz2.cmd, ))

    def testThrowing(self):
        state = GameState(TEAM_LTR, simplified_throwing_directions)
        same_pt = P(5000,2000)
        wiz, wiz2, _, _ = mk_default_wizards()
        snaf = mk_default_entity(p=same_pt)
        wiz.p, wiz.state, wiz.target = same_pt, STATE_WITH_SNAFFLE, snaf
        state.update((wiz, wiz2, snaf))
        state.set_targets()
        expected_aim = state.guess_throw(same_pt, RIGHT)
        self.assertIsInstance(wiz.cmd, CmdThrow)
        self.assertEqual(expected_aim, wiz.cmd.aim)

    def testThrowingSafely(self):
        state = GameState(TEAM_LTR, simplified_throwing_directions)
        same_pt = P(5000,2000)
        wiz, wiz2, op1, _ = mk_default_wizards()
        snaf = mk_default_entity(p=same_pt)
        wiz.p, wiz.state, wiz.target = same_pt, STATE_WITH_SNAFFLE, snaf
        op1.p = P(6000, 2000)
        state.update((wiz, wiz2, op1, snaf))
        state.set_targets()
        expected_aim = state.guess_throw(same_pt, DOWN)
        self.assertIsInstance(wiz.cmd, CmdThrow)
        #self.assertEqual(expected_aim, wiz.cmd.aim)

    def testObliviate(self):
        pass
        # Should execute obliviate when bludger is closing in.


if __name__ == '__main__':
    unittest.main()
