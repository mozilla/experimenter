import mock
from django.test import TestCase


from experimenter.experiments.models import ExperimentVariant
from experimenter.experiments.tests.factories import (
    ExperimentControlFactory,
    ExperimentFactory,
)
from experimenter.experiments.admin import (
    BaseVariantInlineAdmin,
    ControlVariantInlineAdmin,
    ExperimentVariantInlineAdmin,
    ControlVariantModelForm,
)


class BaseVariantInlineAdminTest(TestCase):

    def test_has_no_delete_permissions(self):
        inline_admin = BaseVariantInlineAdmin(mock.Mock(), mock.Mock())
        self.assertFalse(inline_admin.has_delete_permission(mock.Mock()))


class ControlVariantModelFormTests(TestCase):

    def test_save_sets_is_control_to_True(self):
        experiment = ExperimentFactory.create()

        variant_data = ExperimentControlFactory.attributes()
        variant_data['experiment'] = experiment.id
        variant_data['is_control'] = False

        form = ControlVariantModelForm(data=variant_data)

        self.assertTrue(form.is_valid())
        self.assertFalse(form.instance.is_control)

        instance = form.save()

        self.assertTrue(instance.is_control)


class ControlVariantInlineAdminTest(TestCase):

    def test_queryset_filters_is_control_True(self):
        ExperimentFactory.create_with_variants()

        self.assertEqual(ExperimentVariant.objects.all().count(), 2)

        control_admin = ControlVariantInlineAdmin(mock.Mock(), mock.Mock())
        variants = control_admin.get_queryset(mock.Mock())
        self.assertEqual(variants.count(), 1)
        self.assertEqual(variants.filter(is_control=True).count(), 1)
        self.assertEqual(variants.filter(is_control=False).count(), 0)


class ExperimentVariantInlineAdminTest(TestCase):

    def test_queryset_filters_is_control_True(self):
        ExperimentFactory.create_with_variants()

        self.assertEqual(ExperimentVariant.objects.all().count(), 2)

        control_admin = ExperimentVariantInlineAdmin(mock.Mock(), mock.Mock())
        variants = control_admin.get_queryset(mock.Mock())
        self.assertEqual(variants.count(), 1)
        self.assertEqual(variants.filter(is_control=False).count(), 1)
        self.assertEqual(variants.filter(is_control=True).count(), 0)
