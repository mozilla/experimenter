import time

import pytest

from nimbus.pages.new_experiment import NewExperiment
from nimbus.pages.home import HomePage


@pytest.mark.nondestructive
def test_create_new_experiment(selenium, base_url):
    selenium.get(base_url)
    home = HomePage(selenium, base_url).wait_for_page_to_load()
    experiment = home.create_new_button()
    experiment.public_name = "name here"
    experiment.hypothesis = "smart stuff here"
    experiment.set_application()
    overview = experiment.save_and_continue()
    overview.public_description = "description stuff"
    overview.risk_mitigation = "http://risk.mitigation"
    branches = overview.save_and_continue()
    branches.reference_branch_name = "name 1"
    branches.reference_branch_description = "a nice experiment"
    branches.remove_branch()
    metrics = branches.save_and_continue()
    audience = metrics.save_and_continue()
    audience.set_channel()
    audience.set_min_version()
    audience.set_targeting()
    audience.percentage = 50.0
    audience.expected_clients = 50
    audience.save_btn()
    time.sleep(1)
    audience.save_and_continue()
    selenium.find_element_by_css_selector("#PageRequestReview")

