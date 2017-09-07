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
    ControlVariantModelForm,
    ExperimentAdmin,
    ExperimentChangeLogInlineAdmin,
    ExperimentVariantInlineAdmin,
    SlugPrepopulatedMixin,
)


class SlugPrepopulatedMixinTest(TestCase):

    class BaseAdmin(object):

        def get_prepopulated_fields(self, request, obj=None):
            return {}

    def test_slug_is_prepopulated_if_its_not_readonly(self):
        class SlugMixinExample(SlugPrepopulatedMixin, self.BaseAdmin):

            def get_readonly_fields(self, request, obj=None):
                return []

        instance = SlugMixinExample()
        prepopulated_fields = instance.get_prepopulated_fields(
            mock.Mock, mock.Mock())
        self.assertIn('slug', prepopulated_fields)

    def test_slug_is_not_prepopulated_if_its_readonly(self):
        class SlugMixinExample(SlugPrepopulatedMixin, self.BaseAdmin):

            def get_readonly_fields(self, request, obj=None):
                return ('slug',)

        instance = SlugMixinExample()
        prepopulated_fields = instance.get_prepopulated_fields(
            mock.Mock, mock.Mock())
        self.assertNotIn('slug', prepopulated_fields)


class BaseVariantInlineAdminTest(TestCase):

    def test_has_no_delete_permissions(self):
        inline_admin = BaseVariantInlineAdmin(mock.Mock(), mock.Mock())
        self.assertFalse(inline_admin.has_delete_permission(mock.Mock()))

    def test_get_readonly_fields_when_experiment_is_created(self):
        experiment = ExperimentFactory.create_with_variants()

        inline_admin = BaseVariantInlineAdmin(mock.Mock(), mock.Mock())
        inline_admin.readonly_fields = ('a', 'b', 'c')
        inline_admin.fields = ('a', 'b', 'c', 'd', 'e')

        readonly_fields = inline_admin.get_readonly_fields(
            mock.Mock(), obj=experiment)
        self.assertEqual(
            set(readonly_fields), set(inline_admin.readonly_fields))

    def test_get_readonly_fields_when_experiment_is_readonly(self):
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_PENDING
        experiment.save()

        inline_admin = BaseVariantInlineAdmin(mock.Mock(), mock.Mock())
        inline_admin.readonly_fields = ('a', 'b', 'c')
        inline_admin.fields = ('a', 'b', 'c', 'd', 'e')

        readonly_fields = inline_admin.get_readonly_fields(
            mock.Mock(), obj=experiment)
        self.assertEqual(set(readonly_fields), set(inline_admin.fields))

    def test_get_fieldsets_return_fields_when_experiment_created(self):
        experiment = ExperimentFactory.create_with_variants()

        inline_admin = BaseVariantInlineAdmin(mock.Mock(), mock.Mock())
        inline_admin.fields = ('a', 'b', 'c')

        fieldsets = inline_admin.get_fieldsets(mock.Mock(), obj=experiment)
        self.assertEqual(fieldsets, [(None, {'fields': ('a', 'b', 'c')})])

    def test_get_fieldsets_return_one_row_when_experiment_readonly(self):
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_PENDING
        experiment.save()

        inline_admin = BaseVariantInlineAdmin(mock.Mock(), mock.Mock())
        inline_admin.fields = ('a', 'b', 'c')

        fieldsets = inline_admin.get_fieldsets(mock.Mock(), obj=experiment)
        self.assertEqual(fieldsets, ((None, {'fields': (('a', 'b', 'c'),)}),))


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

    def test_queryset_filters_is_control_False(self):
        ExperimentFactory.create_with_variants()

        self.assertEqual(ExperimentVariant.objects.all().count(), 2)

        control_admin = ExperimentVariantInlineAdmin(mock.Mock(), mock.Mock())
        variants = control_admin.get_queryset(mock.Mock())
        self.assertEqual(variants.count(), 1)
        self.assertEqual(variants.filter(is_control=False).count(), 1)
        self.assertEqual(variants.filter(is_control=True).count(), 0)


class ExperimentChangeLogInlineAdminTest(TestCase):

    def test_has_no_add_permission(self):
        change_admin = ExperimentChangeLogInlineAdmin(mock.Mock(), mock.Mock())
        self.assertFalse(change_admin.has_add_permission(mock.Mock()))

    def test_has_no_delete_permission(self):
        change_admin = ExperimentChangeLogInlineAdmin(mock.Mock(), mock.Mock())
        self.assertFalse(change_admin.has_delete_permission(mock.Mock()))


class ExperimentAdminTest(TestCase):

    def test_no_actions(self):
        experiment_admin = ExperimentAdmin(mock.Mock(), mock.Mock())
        self.assertEqual(experiment_admin.get_actions(mock.Mock()), [])

    def test_no_delete_permission(self):
        experiment_admin = ExperimentAdmin(mock.Mock(), mock.Mock())
        self.assertFalse(experiment_admin.has_delete_permission(mock.Mock()))

    def test_show_dashboard_url_returns_link(self):
        experiment_admin = ExperimentAdmin(mock.Mock(), mock.Mock())
        experiment = ExperimentFactory.create_with_variants()
        self.assertEqual(
            experiment_admin.show_dashboard_url(experiment),
            '<a href="{url}" target="_blank">{url}</a>'.format(
                url=experiment.dashboard_url)
        )

    def test_readonly_fields_for_created_experiment(self):
        experiment_admin = ExperimentAdmin(mock.Mock(), mock.Mock())
        experiment = ExperimentFactory.create_with_variants()

        readonly_fields = experiment_admin.get_readonly_fields(
            request=mock.Mock(), obj=experiment)
        self.assertNotIn('status', readonly_fields)
        self.assertNotIn('project', readonly_fields)
        self.assertNotIn('name', readonly_fields)
        self.assertNotIn('slug', readonly_fields)

    def test_readonly_fields_for_readonly_experiment(self):
        experiment_admin = ExperimentAdmin(mock.Mock(), mock.Mock())
        experiment = ExperimentFactory.create_with_variants()
        experiment.status = experiment.STATUS_PENDING
        experiment.save()

        readonly_fields = experiment_admin.get_readonly_fields(
            request=mock.Mock(), obj=experiment)
        self.assertNotIn('status', readonly_fields)
        self.assertIn('project', readonly_fields)
        self.assertIn('name', readonly_fields)
        self.assertIn('slug', readonly_fields)

    def test_status_fields_not_shown_for_new_experiment(self):
        experiment_admin = ExperimentAdmin(mock.Mock(), mock.Mock())

        fieldsets = experiment_admin.get_fieldsets(mock.Mock(), obj=None)
        self.assertNotIn('Status', [fieldset[0] for fieldset in fieldsets])

    def test_status_fields_shown_for_created_experiment(self):
        experiment_admin = ExperimentAdmin(mock.Mock(), mock.Mock())

        fieldsets = experiment_admin.get_fieldsets(
            mock.Mock(), obj=mock.Mock())
        self.assertIn('Status', [fieldset[0] for fieldset in fieldsets])
