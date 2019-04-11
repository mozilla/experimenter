# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change.

## Code of Conduct

Please note we have a [Code of Conduct](https://www.mozilla.org/en-US/about/governance/policies/participation/), please follow it in all your interactions with the project.

## Filing an Issue

1. Look for a similar issue that may already exist.

1. If none exists, create a new issue and provide as much description and context as possible.

1. Apply any relevant labels to the issue and set the milestone to Backlog.

## Pull Request Process

1. Find the issue you want to work on.  If no relevant issue exists, see above and file an
issue, then continue to the next step.

1. Assign the issue to yourself, and change the milestone from Backlog to the currently active
milestone.

1. Create a branch in your local fork with the issue number in the name.

1. Implement the code changes described by the issue.  All Python code changes should
be accompanied by any relevant tests, either by modifying existing ones or adding new
ones.  Front-end changes (HTML/CSS/JS), and infrastructure changes (Docker related things)
do not require tests.

1. When all your changes are complete to your satisfaction:
  - Run `make check` to run the full test, linting, formatting, and coverage suites.
  - Fix any linting issues by running `make code_format` or by hand if the auto formatter is unable to fix it.
  - Fix any broken tests
  - Ensure coverage remains at 100% by adding new tests for any uncovered lines.

1. When all tests and checks are passing, commit all your changes into a single commit and name
the commit with a brief description of the change and `fixes #123` where `#123` is the issue number.
You can add any additional descriptive information to the message body of the commit, but the issue
number must be present in the first line of the commit.  Example: `Add new dashboard link fixes #123`

1. Push your branch up to your fork and submit a pull request on to master.  Add any additional
information you'd like to the pull request body, including descriptions of changes, screenshots
of any UI changes, special instructions for testing, etc.

1. Find a reviewer.  If you're not sure who should review, please contact us on #experimenter on
[IRC](https://wiki.mozilla.org/IRC).

1. If you receive feedback that requires changes to your pull request, make the changes locally,
run `make check` again to ensure all tests and linting are passing, and then create a new commit
that describes what feedback was addressed.  This commit can be formatted however you like, it will
be squashed before it is merged into master.

1. When your pull request is approved, it can be closed by using the 'Squash and Merge' button to
squash all of the commits into a single one that refers to both the issue and the pull request and
contains any additional descriptive information.

1. Thank you for submitting changes to Experimenter :D
