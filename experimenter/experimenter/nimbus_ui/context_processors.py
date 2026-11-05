from experimenter.experiments.constants import EXTERNAL_URLS, RISK_QUESTIONS
from experimenter.nimbus_ui.constants import TYPE_ICON_MAP, NimbusUIConstants


def nimbus_ui_constants(request):
    """
    Context processor that makes NimbusUIConstants, EXTERNAL_URLS,
    RISK_QUESTIONS, and TYPE_ICON_MAP available to all templates.

    This allows templates to access UI constants directly via:
    {{ NimbusUIConstants.PROPERTY_NAME }}
    {{ EXTERNAL_URLS.URL_KEY }}
    {{ RISK_QUESTIONS.QUESTION_KEY }}
    {{ TYPE_ICON_MAP.Experiment.icon }}
    """
    return {
        "NimbusUIConstants": NimbusUIConstants,
        "EXTERNAL_URLS": EXTERNAL_URLS,
        "RISK_QUESTIONS": RISK_QUESTIONS,
        "TYPE_ICON_MAP": TYPE_ICON_MAP,
    }
