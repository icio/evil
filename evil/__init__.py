#!/usr/bin/env python
from collections import OrderedDict
import fnmatch
import os
import re

# Operators which act on expressions to their right are OP_RIGHT operators.
# Operators which act on expressions to their left are OP_LEFT operators.
# Operators which act on both are OP_LEFT | OP_RIGHT = OP_BOTH.
OP_LEFT, OP_RIGHT, OP_BOTH = 1, 2, 3


def evil(expr, lookup, operators, cast, reducer, tokenizer):
    """evil evaluates an expression according to the eval description given.

    :param expr: An expression to evaluate.
    :param lookup: A callable which takes a single pattern argument and returns
                   a set of results. The pattern can be anything that is not an
                   operator token or round brackets.
    :param operators: A precedence-ordered dictionary of (function, side)
                      tuples keyed on the operator token.
    :param reducer: A callable which takes a sequential list of values (from
                    operations or lookups) and combines them into a result.
                    Typical behaviour is that of the + operator. The return
                    type should be the same as cast.
    :param cast: A callable which transforms the results of the lookup into
                 the type expected by the operators and the type of the result.
    :param tokenizer: A callable which will break the query into tokens for
                      evaluation per the lookup and operators. Defaults to
                      setquery.query_tokenizer.
    :raises: SyntaxError
    :returns:

    """
    operators = OrderedDict((op[0], op[1:]) for op in operators)
    if "(" in operators or ")" in operators:
        raise ValueError("( and ) are reserved operators")

    operator_tokens = ["(", ")"] + operators.keys()
    tokens = iter(tokenizer(expr, operator_tokens))
    levels = [[]]

    while True:
        # Token evaluation and pattern lookups

        expr = levels.pop()           # The currently-constructed expression
        new_level = False             # We should step into a subexpression
        first_token = len(expr) == 0  # The first (sub)exp. token

        prev_op_side = None           # The side of the last-seen operator
        try:
            # Try to get the side of the last operator from an expression
            # which we are going to continue constructing.
            prev_op_side = operators[expr[-1]][1]
        except:
            pass

        for token in tokens:

            if token == "(":
                new_level = True
                break
            elif token == ")":
                break
            elif token in operators:
                op_side = operators[token][1]
                if first_token and op_side & OP_LEFT:
                    raise SyntaxError("Operators which act on expressions to "
                                      "their left or both sides cannot be at "
                                      "the beginning of an expression.")
                if prev_op_side is not None:
                    if prev_op_side & OP_RIGHT and op_side & OP_LEFT:
                        raise SyntaxError("Operators cannot be beside one "
                                          "another if they act on expressions "
                                          "facing one-another.")
                expr.append(token)
                prev_op_side = op_side
                continue
            else:
                expr.append(cast(lookup(token)))
                prev_op_side = None

            first_token = False

        if new_level:
            levels.append(expr)
            levels.append([])
            continue
        elif prev_op_side is not None and prev_op_side & OP_RIGHT:
            raise SyntaxError("Operators which act on expressions to their "
                              "right or both sides cannot be at the end of "
                              "an expression.")

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

        if len(levels) > 0:
            levels[-1].append(reducer(expr))
        else:
            break

    return reducer(expr)


def expr_tokenizer(expr, operator_tokens):
    """expr_tokenizer yields the components ("tokens") forming the expression.

    Tokens are split by whitespace which is never considered a token in its
    own right. operator_tokens should likely include "(" and ")" and strictly
    the expression. This means that the word 'test' will be split into ['t',
    'e', 'st'] if 'e' is an operator.

    :param expr: The expression to break into tokens.
    :param operator_tokens: A list of operators to extract as tokens.
    """
    operator_tokens.sort(key=len, reverse=True)
    for m in re.finditer(
        r"""(\s+) |            # Whitespace
            ({0}) |            # Operators
            (.+?)(?={0}|\s|$)  # Patterns
            """.format("|".join(re.escape(op) for op in operator_tokens)),
        expr, re.X
    ):
        token = m.group(2) or m.group(3)
        if token:
            yield token


def op(token, func, left=False, right=False):
    """op provides a more verbose syntax for declaring operators.

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
    """strlookup finds items in the given space matching the given pattern.

    :param pattern: The pattern we wish to match by, per fnmatch.
    :param space: The superset of patterns matching the given items

    """
    return fnmatch.filter(space, pattern)


def globlookup(pattern, root):
    """globlookup finds filesystem objects whose relative path matches the
    given pattern.

    :param pattern: The pattern to wish to match relative filepaths to.
    :param root: The root director to search within.

    """
    for subdir, dirnames, filenames in os.walk(root):
        d = subdir[len(root) + 1:]
        files = (os.path.join(d, f) for f in filenames)
        for f in fnmatch.filter(files, pattern):
            yield f
