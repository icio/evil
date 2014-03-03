from functools import partial
from tempfile import mkdtemp
from unittest import TestCase
import os

from tests import eq_

from evil import strlookup, globlookup
from evil.set import set_evil


class EvilSetTestCase(TestCase):

    def test_set_evil(self):
        lookup = partial(strlookup, space=[
            "a.a.a", "a.a.b", "a.a.c", "a.b.a", "a.b.b", "a.b.c", "a.c.a",
            "a.c.b", "a.c.c", "b.a.a", "b.a.b", "b.a.c", "b.b.a", "b.b.b",
            "b.b.c", "b.c.a", "b.c.b", "b.c.c", "c.a.a", "c.a.b", "c.a.c",
            "c.b.a", "c.b.b", "c.b.c", "c.c.a", "c.c.b", "c.c.c",
        ])
        eq_(set_evil("a.a.*", lookup), set(["a.a.a", "a.a.b", "a.a.c"]))
        eq_(set_evil("a.*.a", lookup), set(["a.a.a", "a.b.a", "a.c.a"]))

        eq_(set_evil("a.a.* = a.*.a", lookup),
            set(["a.a.a"]))
        eq_(set_evil("a.a.* + a.*.a", lookup),
            set(["a.a.a", "a.a.b", "a.a.c", "a.b.a", "a.c.a"]))
        eq_(set_evil("a.a.* - a.*.a", lookup),
            set(["a.a.b", "a.a.c"]))
        eq_(set_evil("a.*.a - a.a.*", lookup),
            set(["a.b.a", "a.c.a"]))
        eq_(set_evil("(a.*) = (a.b.*) = (a.b.c)", lookup),
            set(["a.b.c"]))
        eq_(set_evil("(a.* + b.*) = (*.b.*, *.c.*) = *.c", lookup),
            set(["a.b.c", "a.c.c", "b.b.c", "b.c.c"]))

    def test_globlookup(self):
        # Create temporary files equivalent to those used in test_strlookup
        tmp = mkdtemp()
        chars = ("a", "b", "c")
        for l1 in chars:
            os.mkdir(os.path.join(tmp, l1))
            for l2 in chars:
                os.mkdir(os.path.join(tmp, l1, l2))
                for l3 in chars:
                    f = os.path.join(tmp, l1, l2, l3)
                    with open(f, "w") as fh:
                        fh.write(f)

        # Test the lookup
        lookup = partial(globlookup, root=tmp)
        eq_(list(lookup("a/a/*")), ["a/a/a", "a/a/b", "a/a/c"])
        eq_(list(lookup("a/*/a")), ["a/a/a", "a/b/a", "a/c/a"])
        eq_(list(lookup("*/a/a")), ["a/a/a", "b/a/a", "c/a/a"])
        eq_(list(lookup("a/*")), [
            "a/a/a", "a/a/b", "a/a/c",
            "a/b/a", "a/b/b", "a/b/c",
            "a/c/a", "a/c/b", "a/c/c",
            ])

        # Test the lookup within set_evil
        eq_(set_evil("a/* = */a", lookup), set(["a/a/a", "a/b/a", "a/c/a"]))
