from functools import partial
from nose.tools import eq_, raises
from tempfile import mkdtemp
import os

from setquery import globlookup
from setquery import op
from setquery import OP_BOTH, OP_LEFT, OP_RIGHT
from setquery import query_tokenizer
from setquery import setquery
from setquery import set_operators
from setquery import strlookup


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


def test_query_tokenizer():
    eq_(
        list(query_tokenizer(
            "^^ ^ (a, b + c)",
            ["^", "^^", "(", ")", "+", "-", ","]
        )),
        ["^^", "^", "(", "a", ",", "b", "+", "c", ")"]
    )
    eq_(
        list(query_tokenizer(
            "^ ^ ^ (a, b + c)",
            ["^", "^^", "(", ")", "+", "-", ","]
        )),
        ["^", "^", "^", "(", "a", ",", "b", "+", "c", ")"]
    )


@raises(ValueError)
def test_setquery_bad_operators():
    try:
        setquery("a", lambda: 0, [("(", lambda: 0, 1)])
    except ValueError:
        setquery("a", lambda: 0, [(")", lambda: 0, 1)])


def left_right_ops():
    return [
        op("<", lambda a: set(), left=True),
        op(">", lambda a: set(), right=True),
        op("<>", lambda a, b: set()),
    ]


def test_setquery_left_right():
    eq_(setquery("> b", lambda t: set(), left_right_ops()), set())
    eq_(setquery("a <", lambda t: set(), left_right_ops()), set())
    eq_(setquery("a <> b", lambda t: set(), left_right_ops()), set())


@raises(SyntaxError)
def test_setquery_op_left_missing():
    try:
        setquery("< b", lambda t: set(), left_right_ops())
    except TypeError as e:
        eq_(e.args[0], "Operators which act on expressions to their "
                       "left or both sides cannot be at the beginning "
                       "of an expression.")
        raise e


@raises(SyntaxError)
def test_setquery_op_right_missing():
    try:
        setquery("a >", lambda t: set(), left_right_ops())
    except SyntaxError as e:
        eq_(e.args[0], "Operators which act on expressions to their "
                       "right or both sides cannot be at the end of "
                       "an expression.")
        raise e


@raises(SyntaxError)
def test_setquery_op_either_missing():
    try:
        setquery("a <>", lambda t: set(), left_right_ops())
    except TypeError:
        setquery("<> b", lambda t: set(), left_right_ops())


@raises(SyntaxError)
def test_setquery_op_opposing():
    try:
        setquery("a > < b", lambda t: set(), left_right_ops())
    except SyntaxError as e:
        eq_(e.args[0], "Operators cannot be beside one another if they act on "
                       "expressions facing one-another.")
        setquery("a <> <> b", lambda t: set(), left_right_ops())


def test_setquery_op_double():
    eq_(setquery("a > > b", lambda t: set(), left_right_ops()), set())
    eq_(setquery("a < < b", lambda t: set(), left_right_ops()), set())


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


def test_globlookup():
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

    # Test the lookup within setquery
    eq_(setquery("a/* = */a", lookup), set(["a/a/a", "a/b/a", "a/c/a"]))


def test_daclookup():
    def node_dependencies(node, graph):
        yield node
        for depnode in graph[node]:
            for depdepnode in node_dependencies(depnode, graph):
                yield depdepnode

    # Create a DAC where each node has dependencies declared by name
    # +-----+       +-----+
    # | b.b |       | c.b |
    # +-----+       +-----+
    #   |               |
    #   v               v
    # +-----+       +-----+
    # | b.a |       | c.a |
    # +-----+       +-----+
    #   |               |
    #   |    +-----+    |
    #   +--> | a.b | <--+
    #        +-----+
    #           |
    #           v
    #        +-----+
    #        | a.a |
    #        +-----+
    graph = {
        "a.a": [],
        "a.b": ["a.a"],
        "b.a": ["a.b"],
        "b.b": ["b.a"],
        "c.a": ["a.b"],
        "c.b": ["c.a"],
    }

    # The node lookup
    node_lookup = partial(strlookup, space=graph.keys())

    # The node operators. dependency_op returns the given node and all other
    # nodes up the chain from it.
    dependency_op = lambda nodes: set(
        dep for node in nodes for dep in node_dependencies(node, graph)
    )
    node_operators = [op("^", dependency_op, right=True)] + set_operators()

    # Assert that the node and dependency lookups are working
    eq_(set(node_lookup("a.*")), set(["a.a", "a.b"]))
    eq_(
        set(dependency_op(node_lookup("*.a"))),
        set(["a.a", "a.b", "b.a", "c.a"])
    )

    # (Nodes matching *.a of (the dependencies of (all nodes matching *.b)))
    eq_(
        setquery("^*.b = *.a", node_lookup, node_operators),
        set(["a.a", "b.a", "c.a"])
    )
