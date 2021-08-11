from django.views.generic import TemplateView


class ExperimentReportView(TemplateView):
    template_name = "reporting.html"