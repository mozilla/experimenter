from django.template import Context, Template
from django.test import TestCase


class TestGetItemFilter(TestCase):
    def test_get_item_from_dict_with_valid_key(self):
        template = Template("{% load error_helpers %}{{ data|get_item:key }}")
        context = Context({"data": {"foo": "bar", "baz": 42}, "key": "foo"})
        self.assertEqual(template.render(context), "bar")

    def test_get_item_from_dict_with_missing_key(self):
        template = Template("{% load error_helpers %}{{ data|get_item:key }}")
        context = Context({"data": {"foo": "bar"}, "key": "missing"})
        self.assertEqual(template.render(context), "None")

    def test_get_item_from_list_with_valid_index(self):
        template = Template("{% load error_helpers %}{{ data|get_item:index }}")
        context = Context({"data": ["a", "b", "c"], "index": 1})
        self.assertEqual(template.render(context), "b")

    def test_get_item_from_list_with_invalid_index(self):
        template = Template("{% load error_helpers %}{{ data|get_item:index }}")
        context = Context({"data": ["a", "b"], "index": 5})
        self.assertEqual(template.render(context), "None")

    def test_get_item_with_none_input(self):
        template = Template("{% load error_helpers %}{{ data|get_item:key }}")
        context = Context({"data": None, "key": "foo"})
        self.assertEqual(template.render(context), "None")

    def test_get_item_with_non_dict_non_list(self):
        template = Template("{% load error_helpers %}{{ data|get_item:key }}")
        context = Context({"data": "string", "key": 0})
        self.assertEqual(template.render(context), "s")

    def test_get_item_with_truly_non_indexable(self):
        template = Template("{% load error_helpers %}{{ data|get_item:key }}")
        context = Context({"data": 123, "key": 0})
        self.assertEqual(template.render(context), "None")


class TestGetBranchErrorsTag(TestCase):
    def test_get_reference_branch_errors(self):
        template = Template(
            "{% load error_helpers %}"
            "{% get_branch_errors validation_errors True 0 as errors %}"
            "{{ errors.description.0 }}"
        )
        validation_errors = {
            "reference_branch": {"description": ["Reference error"]},
            "treatment_branches": [{"description": ["Treatment error"]}],
        }
        context = Context({"validation_errors": validation_errors})
        self.assertEqual(template.render(context), "Reference error")

    def test_get_treatment_branch_errors_first_branch(self):
        template = Template(
            "{% load error_helpers %}"
            "{% get_branch_errors validation_errors False 0 as errors %}"
            "{{ errors.description.0 }}"
        )
        validation_errors = {
            "reference_branch": {"description": ["Reference error"]},
            "treatment_branches": [
                {"description": ["Treatment A error"]},
                {"description": ["Treatment B error"]},
            ],
        }
        context = Context({"validation_errors": validation_errors})
        self.assertEqual(template.render(context), "Treatment A error")

    def test_get_treatment_branch_errors_second_branch(self):
        template = Template(
            "{% load error_helpers %}"
            "{% get_branch_errors validation_errors False 1 as errors %}"
            "{{ errors.description.0 }}"
        )
        validation_errors = {
            "treatment_branches": [
                {"description": ["Treatment A error"]},
                {"description": ["Treatment B error"]},
            ],
        }
        context = Context({"validation_errors": validation_errors})
        self.assertEqual(template.render(context), "Treatment B error")

    def test_get_branch_errors_with_empty_validation_errors(self):
        template = Template(
            "{% load error_helpers %}"
            "{% get_branch_errors validation_errors False 0 as errors %}"
            "{{ errors }}"
        )
        context = Context({"validation_errors": {}})
        self.assertEqual(template.render(context), "{}")

    def test_get_branch_errors_with_invalid_index(self):
        template = Template(
            "{% load error_helpers %}"
            "{% get_branch_errors validation_errors False 10 as errors %}"
            "{{ errors }}"
        )
        validation_errors = {
            "treatment_branches": [{"description": ["Treatment error"]}],
        }
        context = Context({"validation_errors": validation_errors})
        self.assertEqual(template.render(context), "{}")

    def test_get_branch_errors_with_none_treatment_branches(self):
        template = Template(
            "{% load error_helpers %}"
            "{% get_branch_errors validation_errors False 0 as errors %}"
            "{{ errors }}"
        )
        validation_errors = {"treatment_branches": None}
        context = Context({"validation_errors": validation_errors})
        self.assertEqual(template.render(context), "{}")

    def test_get_branch_errors_feature_values(self):
        template = Template(
            "{% load error_helpers %}"
            "{% get_branch_errors validation_errors False 0 as errors %}"
            "{{ errors.feature_values.0.value.0 }}"
        )
        validation_errors = {
            "treatment_branches": [
                {"feature_values": [{"value": ["Invalid JSON"]}]},
            ],
        }
        context = Context({"validation_errors": validation_errors})
        self.assertEqual(template.render(context), "Invalid JSON")
