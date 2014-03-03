from functools import partial
from tempfile import mkdtemp
from unittest import TestCase
import os

from tests import eq_, raises

from evil import (
    op,
    OP_BOTH, OP_LEFT, OP_RIGHT,
    expr_tokenizer,
    strlookup,
    globlookup,
)

from evil.set import (
    set_evil,
    set_operators,
)


class EvilTestCase(TestCase):

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

    def test_daclookup(self):
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

        # The node operators. dependency_op returns the given node and all
        # other nodes up the chain from it.
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

        # Nodes matching *.a of (the dependencies of (all nodes matching *.b))
        eq_(
            set_evil("^*.b = *.a", node_lookup, node_operators),
            set(["a.a", "b.a", "c.a"])
        )
