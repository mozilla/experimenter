"""
This type stub file was generated by pyright.
"""

JEXLConfig = ...

def invalidates_grammar(func): ...

class JEXL:
    def __init__(self, context=...) -> None: ...
    @property
    def grammar(self): ...
    @invalidates_grammar
    def add_binary_operator(self, operator, precedence, func): ...
    @invalidates_grammar
    def remove_binary_operator(self, operator): ...
    @invalidates_grammar
    def add_unary_operator(self, operator, func): ...
    @invalidates_grammar
    def remove_unary_operator(self, operator): ...
    def add_transform(self, name, func): ...
    def remove_transform(self, name): ...
    def transform(self, name=...): ...
    def parse(self, expression): ...
    def analyze(self, expression, AnalyzerClass): ...
    def validate(self, expression): ...
    def evaluate(self, expression, context=...): ...
