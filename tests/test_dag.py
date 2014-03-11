from functools import partial
from unittest import TestCase

from tests import eq_

from evil import op, strlookup
from evil.set import set_evil, set_operators


class EvilDAGTestCase(TestCase):

    def test_daglookup(self):
        def node_dependencies(node, graph):
            yield node
            for depnode in graph[node]:
                for depdepnode in node_dependencies(depnode, graph):
                    yield depdepnode

        # Create a DAG where each node has dependencies declared by name
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
