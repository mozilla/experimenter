import pytest


@pytest.mark.skip(reason="failing until we fix gh#4700")
def test_filter_expressions_with_matching_firefox_versions(base_url, selenium):
    selenium.get("about:blank")
    with open("utils/filter_expression.js") as js:
        with selenium.context(selenium.CONTEXT_CHROME):
            script = selenium.execute_script(js.read(), 80.1, 80)
    assert script is True


@pytest.mark.skip(reason="failing until we fix gh#4700")
def test_filter_expressions_with_mismatching_firefox_versions(base_url, selenium):
    selenium.get("about:blank")
    with open("utils/filter_expression.js") as js:
        with selenium.context(selenium.CONTEXT_CHROME):
            script = selenium.execute_script(js.read(), 80.1, 100)
    assert script is False
