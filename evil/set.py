from evil import (
    evil,
    op,
    expr_tokenizer,
)


def set_evil(expr, lookup, operators=None, cast=None, reducer=None,
             tokenizer=None):
    if operators is None:
        operators = set_operators()
    if cast is None:
        cast = set
    if reducer is None:
        reducer = lambda expr: set.union(*expr)
    if tokenizer is None:
        tokenizer = expr_tokenizer
    return evil(expr=expr, lookup=lookup, operators=operators, cast=cast,
                reducer=reducer, tokenizer=tokenizer)


def set_operators():
    return [
        op("=", set.intersection),
        op("+", set.union),
        op("-", set.difference),
        op(",", set.union),
    ]
