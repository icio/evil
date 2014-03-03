from unittest import TestCase

from tests import eq_

from evil.maths import maths_evil


class EvilMathsTestCase(TestCase):
    def test_logic(self):
        eq_(maths_evil("1"), 1)
        eq_(maths_evil("1 < 0"), 0)
        eq_(maths_evil("1 > 0"), 1)
        eq_(maths_evil("0 > 1"), 0)
        eq_(maths_evil("0 < 1"), 1)
        eq_(maths_evil("2 <= 1"), 0)
        eq_(maths_evil("1 <= 1"), 1)
        eq_(maths_evil("0 <= 1"), 1)
        eq_(maths_evil("1 >= 0"), 1)
        eq_(maths_evil("1 >= 1"), 1)
        eq_(maths_evil("1 >= 2"), 0)
        eq_(maths_evil("1 <> 0"), 1)
        eq_(maths_evil("1 <> 1"), 0)

    def test_expr(self):
        eq_(maths_evil("(2 + 2)!"), 24)
        eq_(maths_evil("2 ^ 8"), 256)
        eq_(maths_evil("4 * 10 + 15"), 55)
        eq_(maths_evil("4 * (10 + 15)"), 100)
