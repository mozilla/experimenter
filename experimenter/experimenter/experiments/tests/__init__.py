from pyjexl.jexl import JEXLConfig
from pyjexl.operators import Operator, default_binary_operators, default_unary_operators
from pyjexl.parser import Parser, jexl_grammar

jexl_config = JEXLConfig(
    {},
    default_unary_operators,
    {
        **default_binary_operators,
        "intersect": Operator("intersect", 40, lambda x, y: set(x).intersection(y)),
    },
)


class JEXLParser(Parser):
    grammar = jexl_grammar(jexl_config)

    def __init__(self):
        super().__init__(jexl_config)
