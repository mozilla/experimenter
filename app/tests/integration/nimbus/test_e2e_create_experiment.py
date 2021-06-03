import random

import pytest
from nimbus.pages.home import HomePage


@pytest.mark.nondestructive
def test_create_new_experiment(selenium, base_url):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_new_button()
    experiment.public_name = f"name here {random.randint(0, 100)}"
    experiment.hypothesis = "smart stuff here"
    experiment.application = "DESKTOP"

    # Fill Overview Page
    overview = experiment.save_and_continue()
    overview.public_description = "description stuff"
    overview.select_risk_brand_false()
    overview.select_risk_revenue_false()
    overview.select_risk_partner_false()

    # Fill Branches page
    branches = overview.save_and_continue()
    branches.remove_branch()
    branches.reference_branch_name = "name 1"
    branches.reference_branch_description = "a nice experiment"
    branches.feature_config = "No Feature Firefox Desktop"

    # Fill Metrics page
    metrics = branches.save_and_continue()

    # Fill Audience page
    audience = metrics.save_and_continue()
    audience.channel = "Nightly"
    audience.min_version = 80
    audience.targeting = "US_ONLY"
    audience.percentage = 50.0
    audience.expected_clients = 50
    audience.save_btn()
    audience.save_and_continue()

    # Review
    selenium.find_element_by_css_selector("#PageRequestReview")
