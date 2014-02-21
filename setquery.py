#!/usr/bin/env python
from collections import OrderedDict
import fnmatch
import re


# Operators which act on expressions to their right are OP_RIGHT operators.
# Operators which act on expressions to their left are OP_LEFT operators.
# Operators which act on both are OP_LEFT | OP_RIGHT = OP_BOTH.
OP_LEFT, OP_RIGHT, OP_BOTH = 1, 2, 3


def setquery(query, lookup, operators=None, tokenizer=None):
    """
    :param query: The string query to evaluate
    :param lookup: A callable which takes a single pattern argument and returns
                   a set of results. The pattern can be anything that is not an
                   operator token or round brackets.
    :param operators: A precedence-ordered list of (token, function, side).
                      Where side is OP_BOTH the function should take two args,
                      otherwise it should take one. Defaults to the typical
                      set operators union, intersection, and difference as per
                      the setquery.set_operators.
    :param tokenizer: A callable which will break the query into tokens for
                      evaluation per the lookup and operators. Defaults to
                      setquery.query_tokenizer.
    :raises: ValueError, SyntaxError
    :returns: set

    """
    if tokenizer is None:
        tokenizer = query_tokenizer
    if operators is None:
        operators = set_operators()

    operators = OrderedDict({op[0]: op[1:] for op in operators})
    if "(" in operators or ")" in operators:
        raise ValueError("( and ) are reserved operators")

    operator_tokens = ["(", ")"] + operators.keys()
    tokens = tokenizer("(%s)" % query, operator_tokens)

    return setquery_eval(tokens, lookup, operators)


def set_operators():
    return [
        ("=", set.intersection, OP_BOTH),
        ("+", set.union, OP_BOTH),
        ("-", set.difference, OP_BOTH),
        (",", set.union, OP_BOTH),
        # ("^", lambda right: set(item.deps() for item in right), OP_RIGHT)
    ]


def setquery_eval(tokens, lookup, operators):
    """
    :param tokens: An iterable of string tokens to evaluate.
    :param lookup: A callable which takes a single pattern argument and returns
                   a set of results. The pattern can be anything that is not an
                   operator token or round brackets.
    :param operators: A precedence-ordered dictionary of (function, side)
                      tuples keyed on the operator token.
    :raises: SyntaxError

    """
    # Token evaluation and lookups

    expr = []
    tokens = iter(tokens)
    prev_op_side = None
    for t, token in enumerate(tokens):
        if token == "(":
            expr.append(setquery_eval(tokens, lookup, operators))
        elif token == ")":
            if prev_op_side is not None and prev_op_side & OP_RIGHT:
                raise SyntaxError("Operators which act on expressions to "
                                  "their right or both sides cannot be at "
                                  "the end of an expression.")
            break
        elif token in operators:
            op_side = operators[token][1]
            if t == 0 and op_side & OP_LEFT:
                raise SyntaxError("Operators which act on expressions to "
                                  "their left or both sides cannot be at "
                                  "the beginning of an expression.")
            if prev_op_side is not None:
                if prev_op_side & OP_RIGHT and op_side & OP_LEFT:
                    raise SyntaxError("Operators cannot be beside one another "
                                      "if they act on expressions facing "
                                      "one-another.")
            expr.append(token)
            prev_op_side = op_side
            continue
        else:
            expr.append(set(lookup(token)))
        prev_op_side = None

    # Operator evaluation

    explen = len(expr)
    for op, (op_eval, op_side) in operators.iteritems():
        if op_side is OP_RIGHT:

            # Apply right-sided operators. We loop from the end backward so
            # that multiple such operators next to noe another are resolved
            # in the correct order
            t = explen - 1
            while t >= 0:
                if expr[t] == op:
                    expr[t] = op_eval(expr[t + 1])
                    del expr[t + 1]
                    explen -= 1
                t -= 1

        else:

            # Apply left- and both-sided operators. We loop forward so that
            # that multiple such operators next to one another are resolved
            # in the correct order.
            t = 0
            while t < explen:
                if expr[t] == op:
                    # Apply left- or both-sided operators
                    if op_side is OP_LEFT:
                        expr[t] = op_eval(expr[t - 1])
                        del expr[t - 1]
                        t -= 1
                        explen -= 1
                    elif op_side is OP_BOTH:
                        expr[t] = op_eval(expr[t - 1], expr[t + 1])
                        del expr[t + 1], expr[t - 1]
                        t -= 1
                        explen -= 2
                t += 1

    return expr[0].union(*expr[1:])


def query_tokenizer(query, operator_tokens):
    for m in re.finditer(
        r"""(\s+) |            # Whitespace
            ({0}) |            # Operators
            (.+?)(?={0}|\s|$)  # Patterns
            """.format("|".join(re.escape(op) for op in operator_tokens)),
        query, re.X
    ):
        token = m.group(2) or m.group(3)
        if token:
            yield token


def op(token, func, left=False, right=False):
    """
    A more verbose syntax for declaring operators.

    :param token: The string token of the operator. Usually a single character.
    :param func: A callable used to evaluate its arguments. Where the operator
                 is both-sided the callable should accept two arguments. Where
                 it is one-sided it should accept one argument.
    :param left: A boolean indicating whether the operator applies to the
                 expression to the left of it.
    :param right: A boolean indicating whether the operator applies to the
                  expression to the right of it.
    :returns: a tuple (token, func, side) where side is OP_BOTH if left and
              right (or neither) and OP_LEFT if left, otherwise OP_RIGHT.

    """
    both = (left == right)
    return (token, func, OP_BOTH if both else OP_LEFT if left else OP_RIGHT)


def strlookup(pattern, space):
    return fnmatch.filter(space, pattern)


if __name__ == "__main__":
    help(setquery)
