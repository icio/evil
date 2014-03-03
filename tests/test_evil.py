from functools import partial
from unittest import TestCase

from tests import eq_, raises

from evil import (
    op,
    OP_BOTH, OP_LEFT, OP_RIGHT,
    expr_tokenizer,
    strlookup,
)

from evil.set import (
    set_evil,
)


class EvilHelperTestCase(TestCase):

    def test_op(self):
        def myop(l, r):
            pass
        eq_(op("+", myop), ("+", myop, OP_BOTH))
        eq_(op("+", myop, right=True), ("+", myop, OP_RIGHT))
        eq_(op("+", myop, left=True), ("+", myop, OP_LEFT))
        eq_(op("+", myop, left=True, right=True), ("+", myop, OP_BOTH))

    def test_strlookup(self):
        lookup = partial(strlookup, space=[
            "a.a.a", "a.a.b", "a.a.c", "a.b.a", "a.b.b", "a.b.c", "a.c.a",
            "a.c.b", "a.c.c", "b.a.a", "b.a.b", "b.a.c", "b.b.a", "b.b.b",
            "b.b.c", "b.c.a", "b.c.b", "b.c.c", "c.a.a", "c.a.b", "c.a.c",
            "c.b.a", "c.b.b", "c.b.c", "c.c.a", "c.c.b", "c.c.c",
        ])
        eq_(lookup("a.a.*"), ["a.a.a", "a.a.b", "a.a.c"])
        eq_(lookup("a.*.a"), ["a.a.a", "a.b.a", "a.c.a"])
        eq_(lookup("*.a.a"), ["a.a.a", "b.a.a", "c.a.a"])
        eq_(lookup("a.*"), [
            "a.a.a", "a.a.b", "a.a.c",
            "a.b.a", "a.b.b", "a.b.c",
            "a.c.a", "a.c.b", "a.c.c",
            ])

    def test_expr_tokenizer(self):
        eq_(
            list(expr_tokenizer(
                "^^ ^ (a, b + c)",
                ["^", "^^", "(", ")", "+", "-", ","]
            )),
            ["^^", "^", "(", "a", ",", "b", "+", "c", ")"]
        )
        eq_(
            list(expr_tokenizer(
                "^ ^ ^ (a, b + c)",
                ["^", "^^", "(", ")", "+", "-", ","]
            )),
            ["^", "^", "^", "(", "a", ",", "b", "+", "c", ")"]
        )


class EvilTestCase(TestCase):

    @raises(ValueError)
    def test_set_evil_bad_operators(self):
        try:
            set_evil("a", lambda: 0, [("(", lambda: 0, 1)])
        except ValueError:
            set_evil("a", lambda: 0, [(")", lambda: 0, 1)])

    def left_right_ops(self):
        return [
            op("<", lambda a: set(), left=True),
            op(">", lambda a: set(), right=True),
            op("<>", lambda a, b: set()),
        ]

    def test_set_evil_left_right(self):
        eq_(set_evil("> b", lambda t: set(), self.left_right_ops()), set())
        eq_(set_evil("a <", lambda t: set(), self.left_right_ops()), set())
        eq_(set_evil("a <> b", lambda t: set(), self.left_right_ops()), set())

    @raises(SyntaxError)
    def test_set_evil_op_left_missing(self):
        try:
            set_evil("< b", lambda t: set(), self.left_right_ops())
        except TypeError as e:
            eq_(e.args[0], "Operators which act on expressions to their "
                           "left or both sides cannot be at the beginning "
                           "of an expression.")
            raise e

    @raises(SyntaxError)
    def test_set_evil_op_right_missing(self):
        try:
            set_evil("a >", lambda t: set(), self.left_right_ops())
        except SyntaxError as e:
            eq_(e.args[0], "Operators which act on expressions to their "
                           "right or both sides cannot be at the end of "
                           "an expression.")
            raise e

    @raises(SyntaxError)
    def test_set_evil_op_either_missing(self):
        try:
            set_evil("a <>", lambda t: set(), self.left_right_ops())
        except TypeError:
            set_evil("<> b", lambda t: set(), self.left_right_ops())

    @raises(SyntaxError)
    def test_set_evil_op_opposing(self):
        try:
            set_evil("a > < b", lambda t: set(), self.left_right_ops())
        except SyntaxError as e:
            eq_(e.args[0], "Operators cannot be beside one another if they "
                           "act on expressions facing one-another.")
            set_evil("a <> <> b", lambda t: set(), self.left_right_ops())

    @raises(SyntaxError)
    def test_set_evil_op_right_nested_missing(self):
        try:
            set_evil("(a >) < b", lambda t: set(), self.left_right_ops())
        except SyntaxError as e:
            eq_(e.args[0], "Operators which act on expressions to their "
                           "right or both sides cannot be at the end of an "
                           "expression.")
            set_evil("a (< b)", lambda t: set(), self.left_right_ops())
            raise e

    def test_set_evil_op_double(self):
        eq_(set_evil("a > > b", lambda t: set(), self.left_right_ops()), set())
        eq_(set_evil("a < < b", lambda t: set(), self.left_right_ops()), set())
