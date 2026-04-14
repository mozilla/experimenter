import json
import logging

import sentry_sdk
from pyjexl.jexl import JEXLConfig
from pyjexl.operators import Operator, default_binary_operators, default_unary_operators
from pyjexl.parser import (
    ArrayLiteral,
    BinaryExpression,
    ConditionalExpression,
    FilterExpression,
    Identifier,
    Literal,
    ObjectLiteral,
    Parser,
    Transform,
    UnaryExpression,
    jexl_grammar,
)

logger = logging.getLogger(__name__)


JEXL_CONFIG = JEXLConfig(
    {},
    default_unary_operators,
    {
        **default_binary_operators,
        "intersect": Operator("intersect", 40, lambda x, y: set(x).intersection(y)),
    },
)


class JEXLParser(Parser):
    grammar = jexl_grammar(JEXL_CONFIG)

    def __init__(self):
        super().__init__(JEXL_CONFIG)


def to_str(node):
    """
    Serialize a JEXL tree node back to its string representation
    """
    if type(node) is Identifier:
        subject = f"{to_str(node.subject)}." if node.subject is not None else ""
        if node.relative:
            subject = f".{subject}"
        return f"{subject}{node.value}"
    elif type(node) is Literal:
        return f"{json.dumps(node.value)}"
    elif type(node) is ArrayLiteral:
        return f"[{', '.join([to_str(a) for a in node.value])}]"
    elif type(node) is UnaryExpression:
        return f"({node.operator.symbol}{to_str(node.right)})"
    elif type(node) is BinaryExpression:
        return f"({to_str(node.left)} {node.operator.symbol} {to_str(node.right)})"
    elif type(node) is Transform:
        args = f"({', '.join([to_str(a) for a in node.args])})" if node.args else ""
        return f"{to_str(node.subject)}|{node.name}{args}"
    elif type(node) is FilterExpression:
        return f"{to_str(node.subject)}[{to_str(node.expression)}]"
    elif type(node) is ObjectLiteral:
        items = ", ".join(f"{to_str(k)}: {to_str(v)}" for k, v in node.value.items())
        return f"{{{items}}}"
    elif type(node) is ConditionalExpression:
        return (
            f"({to_str(node.test)} ? "
            f"{to_str(node.consequent)} : "
            f"{to_str(node.alternate)})"
        )
    else:
        raise Exception(f"Unhandled node type: {node}")


def collect_exprs(expr):
    """
    Collect the leaf sub expressions of a JEXL expression
    """
    nodes = [JEXLParser().parse(expr)]
    exprs = set()

    while nodes:
        node = nodes.pop()

        children = list(node.children)
        if isinstance(node, ArrayLiteral):
            children.extend(node.value)

        if children:
            nodes += children
        else:
            exprs.add(to_str(node))

    return exprs


def format_jexl(expression):
    if not expression or expression == "true":
        return expression

    def node_to_str(node):
        if isinstance(node, Identifier):
            subject = f"{node_to_str(node.subject)}." if node.subject else ""
            return f"{'.{subject}' if node.relative else subject}{node.value}"
        if isinstance(node, Literal):
            return json.dumps(node.value)
        if isinstance(node, ArrayLiteral):
            return f"[{', '.join(node_to_str(a) for a in node.value)}]"
        if isinstance(node, Transform):
            args_list = [node_to_str(a) or format_node(a, False, 0) for a in node.args]
            args_str = ", ".join(args_list)
            args = f"({args_str})" if node.args else ""
            subject_str = node_to_str(node.subject) or format_node(node.subject, False, 0)
            return f"{subject_str}|{node.name}{args}"
        if isinstance(node, FilterExpression):
            subject_str = node_to_str(node.subject) or format_node(node.subject, False, 0)
            expr_str = node_to_str(node.expression) or format_node(
                node.expression, False, 0
            )
            return f"{subject_str}[{expr_str}]"
        return None

    def format_node(node, needs_parens=False, indent=0):
        if isinstance(node, BinaryExpression):
            if node.operator.symbol in ("&&", "||"):

                def child_needs_parens(child):
                    return (
                        isinstance(child, BinaryExpression)
                        and child.operator.symbol in ("&&", "||")
                        and child.operator.symbol != node.operator.symbol
                    )

                left_needs = child_needs_parens(node.left)
                right_needs = child_needs_parens(node.right)

                left_indent = indent + 1 if left_needs else indent
                right_indent = indent + 1 if right_needs else indent

                left = format_node(node.left, left_needs, left_indent)
                right = format_node(node.right, right_needs, right_indent)

                right_indented = "\n".join(
                    "  " * indent + line for line in right.split("\n")
                )

                result = f"{left} {node.operator.symbol}\n{right_indented}"

                if needs_parens:
                    close = f"\n{'  ' * (indent - 1)})"
                    return f"(\n{'  ' * indent}{result}{close}"
                return result
            left = node_to_str(node.left) or format_node(node.left, False, indent)
            right = node_to_str(node.right) or format_node(node.right, False, indent)

            if (
                isinstance(node.left, BinaryExpression)
                and node.left.operator.precedence < node.operator.precedence
            ):
                left = f"({left})"
            if (
                isinstance(node.right, BinaryExpression)
                and node.right.operator.precedence <= node.operator.precedence
            ):
                right = f"({right})"

            return f"{left} {node.operator.symbol} {right}"
        if isinstance(node, UnaryExpression):
            right = node_to_str(node.right) or format_node(node.right, False, indent)
            return f"{node.operator.symbol}({right})"
        return node_to_str(node) or str(node)

    try:
        return format_node(JEXLParser().parse(expression))
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logging.exception(f"Failed to parse JEXL expression `{expression}'")

        return expression
