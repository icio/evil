import math
import operator

from evil import (
    evil,
    op,
    expr_tokenizer,
)


def num(n):
    try:
        return int(n)
    except ValueError:
        return float(n)


def maths_evil(expr, lookup=None, operators=None, cast=None, reducer=None,
               tokenizer=None):
    if lookup is None:
        lookup = num
    if operators is None:
        operators = maths_operators()
    if cast is None:
        cast = num
    if reducer is None:
        reducer = sum
    if tokenizer is None:
        tokenizer = expr_tokenizer
    return evil(expr=expr, lookup=lookup, operators=operators, cast=cast,
                reducer=reducer, tokenizer=tokenizer)


def maths_operators():
    return [
        # Numeric operators
        op("!", math.factorial, left=True),
        op("^", operator.pow),
        op("*", operator.mul),
        op("/", operator.truediv),
        op("+", operator.add),
        op("-", operator.sub),
        # Boolean logic operators
        op("==", operator.eq),
        op("<>", operator.ne),
        op(">", operator.gt),
        op("<", operator.lt),
        op(">=", operator.ge),
        op("<=", operator.le),
        # Separator
        op(",", operator.add),
    ]

if __name__ == "__main__":
    import sys
    print maths_evil(" ".join(sys.argv[1:]))
