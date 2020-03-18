import pytest

from pages.base import Base
from pages.home import Home


@pytest.mark.nondestructive
def test_edit_objectives_box(base_url, selenium, fill_overview):
    detail_page = fill_overview.save_btn()
    objectives = detail_page.objective_section.click_edit()
    text = " OBJECTIVELY OBJECTIVE"
    assert text not in objectives.objectives_text_box
    objectives.objectives_text_box = text
    detail_page = objectives.save_btn()
    assert text in detail_page.objective_section.text


@pytest.mark.nondestructive
def test_edit_analysis_box(base_url, selenium, fill_overview):
    detail_page = fill_overview.save_btn()
    analysis = detail_page.analysis_section.click_edit()
    text = "Extra WoRdS"
    assert text not in analysis.analysis_text_box
    analysis.objectives_text_box = " tests for analysis section"
    analysis.analysis_text_box = text
    detail_page = analysis.save_btn()
    assert text in detail_page.analysis_section.text


@pytest.mark.nondestructive
def test_survey_checkbox(base_url, selenium, fill_overview):
    detail_page = fill_overview.save_btn()
    analysis = detail_page.analysis_section.click_edit()
    text = "wurds words werds"
    analysis.objectives_text_box = "testing 1, 2, 3.."
    analysis.analysis_text_box = text
    assert analysis.survey_required_checkbox == "No"
    analysis.survey_required_checkbox = "Yes"
    assert analysis.survey_required_checkbox == "Yes"


@pytest.mark.nondestructive
def test_survey_urls(base_url, selenium, fill_overview):
    detail_page = fill_overview.save_btn()
    analysis = detail_page.analysis_section.click_edit()
    analysis.objectives_text_box = "testing 1, 2, 3.."
    analysis.analysis_text_box = "wurds words werds"
    analysis.survey_required_checkbox = "Yes"
    test_url = "http://www.url.org"
    assert analysis.survey_urls == ""
    analysis.survey_urls = test_url
    detail_page = analysis.save_btn()
    assert test_url in detail_page.analysis_section.survey_urls


@pytest.mark.nondestructive
def test_survey_launch_instructions(base_url, selenium, fill_overview):
    detail_page = fill_overview.save_btn()
    analysis = detail_page.analysis_section.click_edit()
    analysis.objectives_text_box = "testing 1, 2, 3.."
    analysis.analysis_text_box = "wurds words werds"
    analysis.survey_required_checkbox = "Yes"
    analysis.survey_urls = "http://www.url.org"
    assert analysis.survey_launch_instructions == ""
    launch_instructions = "PUSH THE BUTTON"
    analysis.survey_launch_instructions = launch_instructions
    detail_page = analysis.save_btn()
    assert launch_instructions in detail_page.analysis_section.survey_launch_instructions
