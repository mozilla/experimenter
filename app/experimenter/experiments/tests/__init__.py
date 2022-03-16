from pyjexl.jexl import JEXLConfig
from pyjexl.operators import default_binary_operators, default_unary_operators
from pyjexl.parser import Parser, jexl_grammar

jexl_config = JEXLConfig({}, default_unary_operators, default_binary_operators)


class JEXLParser(Parser):
    grammar = jexl_grammar(jexl_config)

    def __init__(self):
        super().__init__(jexl_config)
