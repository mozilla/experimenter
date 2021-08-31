import pytest
from nimbus.pages.home import HomePage
from nimbus.pages.summary import SummaryPage


@pytest.mark.run_once
def test_archive_experiment(
    selenium,
    base_url,
    default_data,
    create_experiment,
):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()

    # Create experiment
    summary_page = create_experiment(selenium, home, default_data)

    # Archive it on the summary page
    summary_page.archive_button.click()

    # Check it's archived on the summary page
    summary_page.wait_for_archive_label_visible()

    # Check it's archived on the directory page
    archived_tab_url = f"{base_url}?tab=archived"
    selenium.get(archived_tab_url)
    home = HomePage(selenium, archived_tab_url).wait_for_page_to_load()
    archived_experiments = home.tables[0]
    assert "Archived" in home.active_tab_text
    for archived_experiment in archived_experiments.experiments:
        if default_data.public_name in archived_experiment.text:
            archived_experiment.click()
            summary_page = SummaryPage(selenium, base_url).wait_for_page_to_load()
            break

    # Unarchive it on the summary page
    summary_page.archive_button.click()

    # Check it's unarchived on the summary page
    summary_page.wait_for_archive_label_not_visible()

    # Check it's in draft on the directory page
    draft_tab_url = f"{base_url}?tab=drafts"
    selenium.get(draft_tab_url)
    home = HomePage(selenium, draft_tab_url).wait_for_page_to_load()
    draft_experiments = home.tables[0]
    assert "Draft" in home.active_tab_text
    for draft_experiment in draft_experiments.experiments:
        if default_data.public_name in draft_experiment.text:
            break
    else:
        raise Exception("Experiment was not found in draft list")
