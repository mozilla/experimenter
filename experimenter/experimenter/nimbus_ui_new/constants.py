class NimbusUIConstants:
    HYPOTHESIS_PLACEHOLDER = """
Hypothesis: If we <do this/build this/create this change in the experiment> for <these users>, then we will see <this outcome>.

We believe this because we have observed <this> via <data source, UR, survey>.

Optional - We believe this outcome will <describe impact> on <core metric>

    """.strip()  # noqa: E501

    ERROR_NAME_INVALID = "This is not a valid name."
    ERROR_SLUG_DUPLICATE = "An experiment with this slug already exists."
    ERROR_HYPOTHESIS_PLACEHOLDER = "Please enter a hypothesis."
