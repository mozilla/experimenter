# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest


@pytest.fixture
def experiment_slug():
    return "firefox-fenix-test-experiment"


@pytest.mark.generic_test
@pytest.mark.xfail(reason="Timeouts due to system lag")
def test_experiment_unenrolls_via_studies_toggle(
    setup_experiment, gradlewbuild, open_app
):
    setup_experiment()
    open_app()
    gradlewbuild.test("GenericExperimentIntegrationTest#disableStudiesViaStudiesToggle")
    gradlewbuild.test("GenericExperimentIntegrationTest#testExperimentUnenrolled")


@pytest.mark.generic_test
def test_experiment_enrolls(
    setup_experiment,
    gradlewbuild,
    open_app,
    check_ping_for_experiment,
):
    setup_experiment()
    open_app()
    gradlewbuild.test("GenericExperimentIntegrationTest#testExperimentEnrolled")
    assert check_ping_for_experiment(reason="enrollment", branch="control")


@pytest.mark.generic_test
def test_experiment_unenrolls_via_secret_menu(
    setup_experiment, gradlewbuild, open_app, check_ping_for_experiment
):
    setup_experiment()
    open_app()
    gradlewbuild.test(
        "GenericExperimentIntegrationTest#testExperimentUnenrolledViaSecretMenu"
    )
    gradlewbuild.test("GenericExperimentIntegrationTest#testExperimentUnenrolled")
    assert check_ping_for_experiment(reason="unenrollment", branch="control")
