import json

from pyjexl.jexl import JEXLConfig
from pyjexl.operators import default_binary_operators, default_unary_operators
from pyjexl.parser import (
    ArrayLiteral,
    BinaryExpression,
    FilterExpression,
    Identifier,
    Literal,
    Parser,
    Transform,
    UnaryExpression,
    jexl_grammar,
)

default_config = JEXLConfig({}, default_unary_operators, default_binary_operators)


class DefaultParser(Parser):
    grammar = jexl_grammar(default_config)

    def __init__(self, config=None):
        super().__init__(config or default_config)


def to_str(node):
    """
    Serialize a JEXL tree node back to its string representation
    """
    if type(node) == Identifier:
        subject = ""
        if node.subject is not None:
            subject = f"{to_str(node.subject)}."
        if node.relative:
            subject = f".{subject}"
        return f"{subject}{node.value}"
    elif type(node) == Literal:
        return f"{json.dumps(node.value)}"
    elif type(node) == ArrayLiteral:
        return f'[{", ".join([to_str(a) for a in node.value])}]'
    elif type(node) == UnaryExpression:
        return f"({node.operator.symbol}{to_str(node.right)})"
    elif type(node) == BinaryExpression:
        return f"({to_str(node.left)} {node.operator.symbol} {to_str(node.right)})"
    elif type(node) == Transform:
        args = ""
        if node.args:
            args = f'({", ".join([to_str(a) for a in node.args])})'
        return f"{to_str(node.subject)}|{node.name}{args}"
    elif type(node) == FilterExpression:
        return f"{to_str(node.subject)}[{to_str(node.expression)}]"
    else:
        raise Exception(f"Unhandled node type: {node}")


def collect_exprs(expr):
    """
    Collect all the sub expressions of a JEXL expression
    """
    nodes = [DefaultParser().parse(expr)]
    exprs = []

    while nodes:
        node = nodes.pop()

        if node.children:
            nodes += list(node.children)

        exprs.append(to_str(node))

    return exprs
