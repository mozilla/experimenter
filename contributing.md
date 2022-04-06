# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change.

## Code of Conduct

Please note we have a [Code of Conduct](https://www.mozilla.org/en-US/about/governance/policies/participation/), please follow it in all your interactions with the project.

## Filing an Issue

1. Look for a similar issue that may already exist.

1. If none exists, create a new issue and provide as much description and context as possible.

1. Apply any relevant labels to the issue.

## Pull Request Process

1. Find the issue you want to work on.  If no relevant issue exists, see above and file an
issue, then continue to the next step.

1. Assign the issue to yourself.

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

1. When all tests and checks are passing, commit all your changes into a single commit and follow the [Git Commit Guidelines](#git-commit-guidelines)

1. Push your branch up to your fork and submit a pull request on to main.  Add any additional
information you'd like to the pull request body, including descriptions of changes, screenshots
of any UI changes, special instructions for testing, etc.

1. Find a reviewer.  If you're not sure who should review, please contact us on #nimbus-dev on
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

## Git Commit Guidelines

### Subject

The subject should follow the this pattern:

`fixes #github_issue_number type(scope): Description`

#### Type
One of the following

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing
  semi-colons, etc)
- **refactor**: A code change that neither fixes a bug or adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests
- **chore**: Changes to the build process or auxiliary tools and libraries such as documentation
  generation

#### Scope

One of the following:

- **project**: Anything that affects the entire project
- **nimbus**: Anything scoped only to Nimbus experiment frontend
- **legacy**: Anything scoped only to Legacy experiment frontend
- **visualization**: Anything scoped only to Analysis Visualization
- **reporting**: Anything scoped to Reporting

#### Description

- use the imperative, present tense: "change" not "changed" nor "changes"
- don't capitalize first letter
- no dot (.) at the end

### Body

The body should describe the purpose of the commit, so that it's clear why this change is being
made. To assist in writing this along with the footer, a git commit template (saved as `~/.gitmessage`)
can be used:

```
Because

* Reason

This commit

* Change
```

Just as in the **subject**, use the imperative, present tense: "change" not "changed" nor "changes". Commits are expected to follow this format.

## Dependency Management
Dependencies are automatically updated by [Dependabot](https://dependabot.com/) which is now integrated
directly into GitHub.  Each week Dependabot will create a large number of individual PRs that update
each dependency in each of the [Experimenter](https://github.com/mozilla/experimenter) and
[Experimenter Docs](https://github.com/mozilla/experimenter-docs) repos.  To merge those into the `main` branch, use the following process:

### Merge Dependabot PRs

#### Manually
1. Dependabot will create many individual PRs against the `main` branch, which must pass all CI checks and be approved before merging.  Approve each PR with the following comment and if they pass CI they will merge automatically:

```
@dependabot squash and merge
```

All done!

#### Automatically
1. Install and configure the [Github CLI](https://github.com/cli/cli)
1. From your local Experimenter repo run

```
make dependabot_approve
```

### Failed Dependabot PRs
If a Dependabot PR fails the CI checks you can either investigate the failure and see if it can be resolved quickly/easily, or close it altogether.

### Security Warnings
Dependabot will also produce [Security Advisories](https://github.com/mozilla/experimenter/security/dependabot) for packages that have registered [CVE](https://en.wikipedia.org/wiki/Common_Vulnerabilities_and_Exposures) numbers.  These can not be resolved automatically.  To resolve the security warnings:

1. Copy the **Remediation** version from the security warning into the `"resolutions"` section of `app/package.json`, example:

    ```js
    "resolutions": {
      "postcss": "^7.0.36",
    ```

1. Update the `yarn.lock` file by running

    ```sh
    yarn install
    ```

1. Commit your changes in a PR titled `chore(deps): Security <list affected packages>`
1. Create a PR and request review
1. Merge when approved

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
