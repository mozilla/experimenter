from experimenter.nimbus_ui.constants import NimbusUIConstants


def nimbus_ui_constants(request):
    """
    Context processor that makes NimbusUIConstants available to all templates.

    This allows templates to access UI constants directly via:
    {{ NimbusUIConstants.PROPERTY_NAME }}
    """
    return {
        "NimbusUIConstants": NimbusUIConstants,
    }
