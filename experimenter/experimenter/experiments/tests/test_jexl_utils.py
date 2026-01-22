from django.test import TestCase

from experimenter.experiments.jexl_utils import format_jexl


class TestFormatJexl(TestCase):
    def test_empty_string(self):
        self.assertEqual(format_jexl(""), "")

    def test_none_value(self):
        self.assertEqual(format_jexl(None), None)

    def test_true_expression(self):
        self.assertEqual(format_jexl("true"), "true")

    def test_simple_expression_no_operators(self):
        result = format_jexl("version >= 100")
        self.assertEqual(result, "version >= 100")

    def test_simple_and_expression(self):
        result = format_jexl("a == 1 && b == 2")
        expected = "a == 1 &&\nb == 2"
        self.assertEqual(result, expected)

    def test_simple_or_expression(self):
        result = format_jexl("a == 1 || b == 2")
        expected = "a == 1 ||\nb == 2"
        self.assertEqual(result, expected)

    def test_multiple_and_expressions(self):
        result = format_jexl("a == 1 && b == 2 && c == 3")
        expected = "a == 1 &&\nb == 2 &&\nc == 3"
        self.assertEqual(result, expected)

    def test_multiple_or_expressions(self):
        result = format_jexl("a == 1 || b == 2 || c == 3")
        expected = "a == 1 ||\nb == 2 ||\nc == 3"
        self.assertEqual(result, expected)

    def test_nested_or_inside_and(self):
        result = format_jexl("a == 1 && (b == 2 || c == 3)")
        expected = """a == 1 &&
(
  b == 2 ||
  c == 3
)"""
        self.assertEqual(result, expected)

    def test_nested_and_inside_or(self):
        result = format_jexl("a == 1 || (b == 2 && c == 3)")
        expected = """a == 1 ||
(
  b == 2 &&
  c == 3
)"""
        self.assertEqual(result, expected)

    def test_deeply_nested_expressions(self):
        result = format_jexl("a == 1 && (b == 2 || (c == 3 && d == 4))")
        expected = """a == 1 &&
(
  b == 2 ||
  (
      c == 3 &&
      d == 4
    )
)"""
        self.assertEqual(result, expected)

    def test_complex_real_world_expression(self):
        expression = (
            'channel == "release" && '
            "(slug in activeRollouts || (isFirstStartup && version >= 100)) && "
            'locale != "en-US"'
        )
        result = format_jexl(expression)
        expected = """channel == "release" &&
(
  slug in activeRollouts ||
  (
      isFirstStartup &&
      version >= 100
    )
) &&
locale != "en-US\""""
        self.assertEqual(result, expected)

    def test_identifier_with_dots(self):
        result = format_jexl('browserSettings.update.channel == "release"')
        self.assertEqual(result, 'browserSettings.update.channel == "release"')

    def test_array_literal(self):
        result = format_jexl("value in [1, 2, 3]")
        self.assertEqual(result, "value in [1, 2, 3]")

    def test_transform_filter(self):
        result = format_jexl('"test"|preferenceValue')
        self.assertEqual(result, '"test"|preferenceValue')

    def test_transform_with_arguments(self):
        result = format_jexl('"test"|preferenceValue(true)')
        self.assertEqual(result, '"test"|preferenceValue(true)')

    def test_transform_with_expression_arguments(self):
        result = format_jexl('["a", b]|bucketSample(x / 1000, 7, 233)')
        self.assertEqual(result, '["a", b]|bucketSample(x / 1000, 7, 233)')

    def test_filter_expression(self):
        result = format_jexl("items[0]")
        self.assertEqual(result, "items[0]")

    def test_filter_expression_with_comparison(self):
        result = format_jexl("items[index > 5]")
        self.assertEqual(result, "items[index > 5]")

    def test_unary_operator(self):
        result = format_jexl("!value")
        self.assertEqual(result, "!(value)")

    def test_unary_with_logical_operators(self):
        result = format_jexl("!a && b")
        expected = "!(a) &&\nb"
        self.assertEqual(result, expected)

    def test_comparison_operators(self):
        result = format_jexl("a > 5 && b < 10 && c >= 3 && d <= 7 && e != 2")
        expected = "a > 5 &&\nb < 10 &&\nc >= 3 &&\nd <= 7 &&\ne != 2"
        self.assertEqual(result, expected)

    def test_string_literals(self):
        result = format_jexl('name == "test-value" && type == "experiment"')
        expected = 'name == "test-value" &&\ntype == "experiment"'
        self.assertEqual(result, expected)

    def test_numeric_literals(self):
        result = format_jexl("version >= 100 && build >= 18362")
        expected = "version >= 100 &&\nbuild >= 18362"
        self.assertEqual(result, expected)

    def test_boolean_literals(self):
        result = format_jexl("enabled == true && verified == false")
        expected = "enabled == true &&\nverified == false"
        self.assertEqual(result, expected)

    def test_mixed_operators_multiple_levels(self):
        expression = "(a || b) && (c || d) && e"
        result = format_jexl(expression)
        expected = """(
  a ||
  b
) &&
(
  c ||
  d
) &&
e"""
        self.assertEqual(result, expected)

    def test_same_and_operator_no_parens(self):
        result = format_jexl("a && b && c")
        expected = "a &&\nb &&\nc"
        self.assertEqual(result, expected)

    def test_same_or_operator_no_parens(self):
        result = format_jexl("a || b || c")
        expected = "a ||\nb ||\nc"
        self.assertEqual(result, expected)
