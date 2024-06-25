from pathlib import Path

import pytest


@pytest.fixture
def filter_expression_path():
    here = Path(__file__).cwd()
    return Path(next(iter(here.glob("**/utils/filter_expression.js"))))


def test_filter_expressions_with_matching_firefox_versions(
    base_url, selenium, filter_expression_path
):
    selenium.get("about:blank")
    with Path(filter_expression_path).open() as js:
        with selenium.context(selenium.CONTEXT_CHROME):
            script = selenium.execute_script(js.read(), 80.1, 80)
    assert script is True


def test_filter_expressions_with_mismatching_firefox_versions(
    base_url, selenium, filter_expression_path
):
    selenium.get("about:blank")
    with Path(filter_expression_path).open() as js:
        with selenium.context(selenium.CONTEXT_CHROME):
            script = selenium.execute_script(js.read(), 80.1, 150)
    assert script is False
