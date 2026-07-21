from experimenter.experiments.constants import EXTERNAL_URLS, RISK_QUESTIONS
from experimenter.nimbus_ui.constants import NimbusUIConstants


def nimbus_ui_constants(request):
    """
    Context processor that makes NimbusUIConstants, EXTERNAL_URLS, and
    RISK_QUESTIONS available to all templates.

    This allows templates to access UI constants directly via:
    {{ NimbusUIConstants.PROPERTY_NAME }}
    {{ EXTERNAL_URLS.URL_KEY }}
    {{ RISK_QUESTIONS.QUESTION_KEY }}
    """
    return {
        "NimbusUIConstants": NimbusUIConstants,
        "EXTERNAL_URLS": EXTERNAL_URLS,
        "RISK_QUESTIONS": RISK_QUESTIONS,
    }
