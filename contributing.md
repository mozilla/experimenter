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
ones.  Front-end changes (HTML/CSS/JS) that involve React code should create or update
any relevant JS tests. Infrastructure changes (Docker related things)
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

1. Push your branch up to your fork and submit a pull request on to main.  Add any additional
information you'd like to the pull request body, including descriptions of changes, screenshots
of any UI changes, special instructions for testing, etc.

1. Find a reviewer.  If you're not sure who should review, please contact us on #experimenter on
the Mozilla Slack if you have access to it.

1. Any PRs that require changes to deployment infrastructure ie environment variable changes,
dependent services, etc also require a review by a member of the operations team.  Please include
any relevant instructions about the changes in the PR.  File a [Bugzilla ticket](https://bugzilla.mozilla.org/enter_bug.cgi?product=Data+Platform+and+Tools&component=Operations) with a link to the PR so that operations can track the change.

1. If you receive feedback that requires changes to your pull request, make the changes locally,
run `make check` again to ensure all tests and linting are passing, and then create a new commit
that describes what feedback was addressed.  This commit can be formatted however you like, it will
be squashed before it is merged into main.

1. When your pull request is approved, it can be closed by using the 'Squash and Merge' button to
squash all of the commits into a single one that refers to both the issue and the pull request and
contains any additional descriptive information.

1. Thank you for submitting changes to Experimenter :D

## Dependency Management
Dependencies are automatically updated by [Dependabot](https://dependabot.com/) which is now integrated
directly into GitHub.  Each week Dependabot will create a large number of individual PRs that update
each dependency.  To merge those into main, use the following process:


### Merge Dependabot PRs
1. Dependabot will create many individual PRs against the `dependencies` branch, which has no 
branch protections and so each of those PRs can be merged automatically by adding the following comment to
each PR:
        @dependabot squash and merge

1. The dependencies branch can now be merged into `main` by [creating a PR using the GitHub web interface](https://github.com/mozilla/experimenter/compare/main...dependencies)

1. Tag a reviewer for the Dependencies PR and when it is approved, merge it.


### Clean up dependencies branch
1. Check out the `main` branch on your local repo:

```
git checkout main
```

1. Make sure it's up to date with the Mozilla remote

```
git pull <mozilla> main
```

1. Delete your local dependencies branch

```
git branch -D dependencies
```

1. Recreate the dependencies branch from your up to date main

```
git checkout -B dependencies
```

1. Force push that on to the Mozilla repo

```
git push <mozilla> dependencies -f
```  

All done!


## Continuous Deployment Process
When a PR is merged into main it will automatically be deployed to the stage instance and if that
is successful then it will automatically be deployed to production.

If the deployment fails at one of the stage/production steps, ops will automatically be paged.

If the deployment succeeds but the change inadvertently breaks stage/production, there are two options:

* Revert the change using a revert commit

  1. Create a branch from main called `revert-#123` where `#123` is the number of the issue, and then
  revert the commit with `git revert <squashed commit hash>`. Fix any potential conflicts or lint/test
  failures and finish the revert commit.

  1. If the original PR included any database migrations, they must be preserved and reverted by creating a new
  subsequent migration

    * `git checkout origin/main -- app/experimenter/experiments/migrations/XXXX_migration_file.py`

    * `make makemigrations`

    * `git add .;git commit -m 'Reverted migration'`

  1. Push the branch and create a PR as normal following the above PR process

* Fix the change following the normal issue/PR processes above

Because all changes will go to stage and prod automatically, you can use stage to validate your changes.
