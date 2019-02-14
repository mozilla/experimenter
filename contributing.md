# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change. 

Please note we have a code of conduct, please follow it in all your interactions with the project.

## Filing an issue

1. Look for a similar issue that may already describe the proposed changes.

1. If none exists, create a new issue and describe the proposed changes.

1. Apply any relevant labels to the issue and set the milestone to Backlog.

## Pull Request Process

1. Find the issue that describes the changes you are going to make.  If no issue exists
for the changes you want to make, see above and file an issue describing the changes, then
continue to the next step.

1. Assign the issue to yourself, and change the milestone from Backlog to the currently active
milestone.

1. Create a branch in your local fork with the issue number in the name.

1. Implement the code changes described by the issue.  All Python code changes should
be accompanied by any relevant tests, either by modifying existing ones or adding new 
ones.  Front-end changes (HTML/CSS/JS), and infrastructure changes (Docker related things)
do not require tests.

1. When all your changes are complete to your satisfaction, run `make check` to run the
full test, linting, formatting, and coverage suites.  Fix any linting issues or breaking tests, 
and make sure coverage remains at 100% by adding new tests for any uncovered lines.

1. When all tests and checks are passing, commit all your changes into a single commit and name 
the commit with a brief description of the change and 'fixes #123' where #123 is the issue number.
You can add any additional descriptive information to the message body of the commit, but the issue 
number must be present in the first line of the commit.  Example: `Add new dashboard link fixes #123`

1. Push your branch up to your fork and submit a pull request on to master.  Add any additional 
information you'd like to the pull request body, including descriptions of changes, screenshots
of any UI changes, special instructions for testing, etc. 

1. Find a reviewer.  If you're not sure who should review, please contact us on #experimenter on
[IRC](https://wiki.mozilla.org/IRC).

1. If you receive feedback that requires changes to your pr, make the changes locally, and then 
ammend them to the commit you submitted rather than adding additional commits.  A PR will only be
merged if the entirety of the change is contained in a single commit that references the issue
number.

1. Thank you for submitting changes to Experimenter :D

### Tagging Process

1. After a milestone is complete and all changes have been merged into master, we can create
a new tag for deployment.

1. Update your local master with the remote master: `git pull origin master`

1. Make sure all checks are passing: `make check`

1. Create a new tag with the milestone version: `git tag vX.YY.0`

1. Push the tag: `git push origin --tags`

1. This will automatically start building a container to deploy and push it to the staging instance
for testing.

## Code of Conduct

### Our Pledge

In the interest of fostering an open and welcoming environment, we as
contributors and maintainers pledge to making participation in our project and
our community a harassment-free experience for everyone, regardless of age, body
size, disability, ethnicity, gender identity and expression, level of experience,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment
include:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behavior by participants include:

* The use of sexualized language or imagery and unwelcome sexual attention or
advances
* Trolling, insulting/derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or electronic
  address, without explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

### Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable
behavior and are expected to take appropriate and fair corrective action in
response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or
reject comments, commits, code, wiki edits, issues, and other contributions
that are not aligned to this Code of Conduct, or to ban temporarily or
permanently any contributor for other behaviors that they deem inappropriate,
threatening, offensive, or harmful.

### Scope

This Code of Conduct applies both within project spaces and in public spaces
when an individual is representing the project or its community. Examples of
representing a project or community include using an official project e-mail
address, posting via an official social media account, or acting as an appointed
representative at an online or offline event. Representation of a project may be
further defined and clarified by project maintainers.

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by contacting the project team at [INSERT EMAIL ADDRESS]. All
complaints will be reviewed and investigated and will result in a response that
is deemed necessary and appropriate to the circumstances. The project team is
obligated to maintain confidentiality with regard to the reporter of an incident.
Further details of specific enforcement policies may be posted separately.

Project maintainers who do not follow or enforce the Code of Conduct in good
faith may face temporary or permanent repercussions as determined by other
members of the project's leadership.

### Attribution

This contributing.md is adapted from https://gist.github.com/PurpleBooth/b24679402957c63ec426

This Code of Conduct is adapted from the [Contributor Covenant][homepage], version 1.4,
available at [http://contributor-covenant.org/version/1/4][version]

[homepage]: http://contributor-covenant.org
[version]: http://contributor-covenant.org/version/1/4/
