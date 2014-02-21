from functools import partial
from nose.tools import eq_, raises

from setquery import argument_default
from setquery import op
from setquery import OP_BOTH, OP_LEFT, OP_RIGHT
from setquery import setquery
from setquery import strlookup


def x(a, b, c=1, d=2):
    pass


def test_argument_default():
    eq_(argument_default(x, "c"), 1)
    eq_(argument_default(x, "d"), 2)


@raises(ValueError)
def test_argument_default_missing():
    try:
        argument_default(x, "e")
    except ValueError as e:
        eq_(e.args, ("%r does not have a parameter %s", x, "e"))
        raise e


@raises(ValueError)
def test_argument_default_unset():
    try:
        argument_default(x, "b")
    except ValueError as e:
        eq_(e.args, ("%r has no default for %s", x, "b"))
        raise e


def test_op():
    def myop(l, r):
        pass
    eq_(op("+", myop), ("+", myop, OP_BOTH))
    eq_(op("+", myop, right=True), ("+", myop, OP_RIGHT))
    eq_(op("+", myop, left=True), ("+", myop, OP_LEFT))
    eq_(op("+", myop, left=True, right=True), ("+", myop, OP_BOTH))


def test_strlookup():
    lookup = partial(strlookup, space=[
        "a.a.a", "a.a.b", "a.a.c", "a.b.a", "a.b.b", "a.b.c", "a.c.a", "a.c.b",
        "a.c.c", "b.a.a", "b.a.b", "b.a.c", "b.b.a", "b.b.b", "b.b.c", "b.c.a",
        "b.c.b", "b.c.c", "c.a.a", "c.a.b", "c.a.c", "c.b.a", "c.b.b", "c.b.c",
        "c.c.a", "c.c.b", "c.c.c",
    ])
    eq_(lookup("a.a.*"), ["a.a.a", "a.a.b", "a.a.c"])
    eq_(lookup("a.*.a"), ["a.a.a", "a.b.a", "a.c.a"])
    eq_(lookup("*.a.a"), ["a.a.a", "b.a.a", "c.a.a"])
    eq_(lookup("a.*"), [
        "a.a.a", "a.a.b", "a.a.c",
        "a.b.a", "a.b.b", "a.b.c",
        "a.c.a", "a.c.b", "a.c.c",
        ])


@raises(ValueError)
def test_setquery_bad_operators():
    try:
        setquery("a", lambda: 0, [("(", lambda: 0, 1)])
    except ValueError:
        setquery("a", lambda: 0, [(")", lambda: 0, 1)])


def left_right_operators():
    return [
        op("<", lambda a: set(), left=True),
        op(">", lambda a: set(), right=True),
        op("<>", lambda a, b: set()),
    ]


def test_setquery_left_right():
    eq_(setquery("> b", lambda t: set(), left_right_operators()), set())
    eq_(setquery("a <", lambda t: set(), left_right_operators()), set())
    eq_(setquery("a <> b", lambda t: set(), left_right_operators()), set())


@raises(SyntaxError)
def test_setquery_op_left_missing():
    try:
        setquery("< b", lambda t: set(), left_right_operators())
    except TypeError as e:
        eq_(e.args[0], "Operators which act on expressions to their "
                       "left or both sides cannot be at the beginning "
                       "of an expression.")
        raise e


@raises(SyntaxError)
def test_setquery_op_right_missing():
    try:
        setquery("a >", lambda t: set(), left_right_operators())
    except SyntaxError as e:
        eq_(e.args[0], "Operators which act on expressions to their "
                       "right or both sides cannot be at the end of "
                       "an expression.")
        raise e


@raises(SyntaxError)
def test_setquery_op_either_missing():
    try:
        setquery("a <>", lambda t: set(), left_right_operators())
    except TypeError:
        setquery("<> b", lambda t: set(), left_right_operators())


@raises(SyntaxError)
def test_setquery_op_opposing():
    try:
        setquery("a > < b", lambda t: set(), left_right_operators())
    except SyntaxError as e:
        eq_(e.args[0], "Operators cannot be beside one another if they act on "
                       "expressions facing one-another.")
        setquery("a <> <> b", lambda t: set(), left_right_operators())


def test_setquery_op_double():
    eq_(setquery("a > > b", lambda t: set(), left_right_operators()), set())
    eq_(setquery("a < < b", lambda t: set(), left_right_operators()), set())


def test_setquery():
    lookup = partial(strlookup, space=[
        "a.a.a", "a.a.b", "a.a.c", "a.b.a", "a.b.b", "a.b.c", "a.c.a", "a.c.b",
        "a.c.c", "b.a.a", "b.a.b", "b.a.c", "b.b.a", "b.b.b", "b.b.c", "b.c.a",
        "b.c.b", "b.c.c", "c.a.a", "c.a.b", "c.a.c", "c.b.a", "c.b.b", "c.b.c",
        "c.c.a", "c.c.b", "c.c.c",
    ])
    eq_(setquery("a.a.*", lookup), set(["a.a.a", "a.a.b", "a.a.c"]))
    eq_(setquery("a.*.a", lookup), set(["a.a.a", "a.b.a", "a.c.a"]))

    eq_(setquery("a.a.* = a.*.a", lookup),
        set(["a.a.a"]))
    eq_(setquery("a.a.* + a.*.a", lookup),
        set(["a.a.a", "a.a.b", "a.a.c", "a.b.a", "a.c.a"]))
    eq_(setquery("a.a.* - a.*.a", lookup),
        set(["a.a.b", "a.a.c"]))
    eq_(setquery("a.*.a - a.a.*", lookup),
        set(["a.b.a", "a.c.a"]))
    eq_(setquery("(a.* + b.*) = (*.b.*, *.c.*) = *.c", lookup),
        set(["a.b.c", "a.c.c", "b.b.c", "b.c.c"]))
