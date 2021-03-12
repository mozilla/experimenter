# Location for the new Experiment "Docs Hub" codebase + docs

- Status: **draft**
- Deciders: Kate Hudson, Jared Lockhart, Lauren Zugai, Tim Smith, Les Orchard, Jody Heavener
- Date: 2021-03-12

## Context and Problem Statement

ADR #5, ["Use Docusaurus + GH Pages for the Nimbus User Doc Hub"](https://github.com/mozilla/experimenter/blob/main/app/experimenter/docs/adrs/0005-doc-hub.md), determined that our approach to setting up a new central location for Experimenter/Nimbus and related project documentation would use [Docusaurus](https://v2.docusaurus.io/), a static site generator, with the static files being served from [GitHub Pages](https://pages.github.com/). While we knew we would be introducing a new set of code we didn't explicitly decide where it would live and what the process for deploying would look like, beyond suggesting it could live in the existing Experimenter repository.

In investigating how to set all of this up we realized there would be certain caveats to hosting and deploying this code from the Experimenter repository, and this lead to the consideration of using a dedicated repository. This ADR outlines our options and end decision.

## Decision Drivers

- How much setup work is involved, both for the code _and_ for integrations or other non-code processes?
- How much overhead and complexity is involved in maintaining this setup, as well as keeping our processes and tools in sync with Experimenter?
- Not everyone who contributes to these docs is a programmer; how much of a learning curve does this present?

## Considered Options

- Use the Experimenter repository, main branch
- Use the Experimenter repository, dedicated branch
- Set up a new, dedicated repository

## Decision Outcome

**Set up a new, dedicated repository**

**Editor's note, 2021-03-12** - This ADR was written after a separate repository was already set up, worked on, and put into use. We've decided to, for approximately one month, use it and see if there is any major fallout. This ADR should be amended with the result of that experiment.

## Pros and Cons of the Options

### Use the Experimenter repository, main branch

This decision would have us use the `mozilla/experimenter` repository, housing the code and documentation files in the `main` branch (likely in a nested `/app/docs` directory), and the built/static files would be committed to and served from a `gh-pages` branch.

Pros

- Everything is under one roof. There is nothing new to clone, no new branches to check out and very little to learn if you're already familiar with Experimenter. You're just pulling in the latest changes and adding new files.
- Using this repository means using its existing integrations; for example, code analysis Actions, Dependabot, Jira, and Sentry with no or minimal setup.
- You could merge changes to both documentation and the Experimenter codebase in the same Pull Request.

Cons

- There is a caveat to "pulling in the latest changes and adding new files": this doesn't necessarily apply to drive-by contributors. If you are someone who regularly works with the Experimenter codebase this should be a familiar process, but if you are someone who only wants to contribute simple documentation or perhaps suggest a change you'll need to first understand what you're looking at [in the repository] and where everything is located.
- The repository is set up to run a set of test and build CircleCI jobs any time a Pull Request is opened (initially, then on new pushes), and again when merging into `main`. They can be expensive with repeated runs, take a non-trivial amount of time, and are subject to hiccups and flaky tests. As such we would likely need to modify our existing CircleCI config to not run certain jobs if changes only occurred in documentation-related files, which could be a considerable amount of work.
    - We _could_ alternatively ignore this altogether; we're under our CircleCI spend and in theory documentation-related runs wouldn't eat up too many credits. This would need to be monitored and evaluated at a later time.
- If we want to utilise Experimenter's existing Yarn workspaces it means we need to place the Docusaurus code underneath the code's `/app` directory as this is where the root Yarn project is. This isn't as ideal as having a `/docs-hub` directory at the root of the project, which would be better for contributors less familiar with the rest of Experimenter.
    - It's also a possibility that we don't need to use Yarn workspaces for this. The downside to that is that we'd then have two distinct Yarn installation processes and `node_modules` directories.
- This hub is intended to provide documentation for a variety of services, and is not just scoped to Experimenter Console. Given that we already have other separate familial repositories it might seem odd to house this hub inside `mozilla/experimenter`.
- Precludes us from using the repository's GitHub Pages path for another project that might be more specific to Experimenter Console.

### Use the Experimenter repository, dedicated branch

This decision would have us use the `mozilla/experimenter` repository, but restrict all code and documentation to a dedicated branch. The dedicated branch would first entirely remove all code coming from the `main` branch, never merging back into it. Built/static code would then either be committed to and served from that same branch or a different branch (e.g. `docs-hub` for development, `gh-pages` for static).

Pros

- Where using the main branch meant configuring CircleCI to not run certain workflows if changes only occurred in documentation files, a dedicated branch means we could entirely remove the CircleCI config. Assuming CircleCI evaluates the config file on each push, if one does not exist it could mean that it won't run at all, mitigating the issue altogether.

Neutral

- This option inherits pros and cons from the two other options, as it is simultaneously part of and not part of `mozilla/experimenter`. It gives us that "fresh" repository setup, while allowing us to use some of the existing integrations. However it also imposes the same idea that it is scoped to the Experimenter Console, adds cultural overhead, has potential CI implications, and introduces its own unique cons.

Cons

- It's effectively a new repository, hidden inside an existing repository, and likely has the greatest learning curve for less-technical contributors.
- Having active development/code and automated commits/static files in the same branch would be messy, but having _two_ dedicated branches for documentation (one for active development, one for static files) would be cumbersome and likely confusing.
- You would not be able to merge changes to both documentation and the Experimenter codebase in the same Pull Request.
- Would mean mixed PRs -- Experimenter and Docs Hub -- that are talking about completely distinct source paths.
- Precludes us from using the repository's GitHub Pages path for another project that might be more specific to Experimenter Console.

### Set up a new, dedicated repository

This decision would have us create a new repository under the Mozilla GitHub org, separate from any other codebase. The active code and documentation files would live in the `main` branch based at the root, and the built/static files would be committed to and served from a `gh-pages` branch.

Pros

- It's a "fresh" repository, allowing us greater initial flexibility in how code is set up, organized, and deployed. Without needing to be shuffled around to accommodate larger changes to the Experimenter Console code it also means greater long-term flexibility.
- Deploys could be done any way we see fit. For example, a simple GitHub Actions workflow could be used. If we chose to use CircleCI like Experimenter does it would be simpler to set up and maintain a new configuration, compared to setting up and making work a new workflow alongside Experimenter's existing CircleCI config.
- Compared to using Experimenter's CircleCI config and needing to wait for jobs unrelated to the doc changes, a standalone deploy process is quicker and less prone to intermittent failures.
- Provides us with a neutral spot for documentation across all projects associated with Experimenter (Nimbus UI, SDKs, Jetstream, etc).

Neutral

- We'd likely need disable requiring signed commits in order to give more flexibility to contributors who might not have GPG signing set up. This is less of a concern as it's not a high-risk codebase, and is partially mitigated by allowing squash commits in the GitHub UI, where GitHub itself signs the merge commit.

Cons

- Adds some cultural overhead as we are introducing Yet Another Repository for individuals to get familiar with, set up notifications for, etc.
- Using a repository separate from `mozilla/experimenter`, or any established repository, involves some technical overhead. This means ensuring correct permissions for contributors, setting up or finding alternate solutions to integrations (e.g. Sentry, Slack, Jira, Dependabot) we decide we need, and individuals needing to clone and install dependencies for the new codebase. We also run the risk of encountering unknowns that have been addressed over time with mature repository.
    - An example of finding an alternate solution to an integration is Jira, and specifically filing issues. Instead of connecting this new repository with Jira we could disable issue filing on the repository and require any new issues be filed under the EXP project in Jira, having them sync to `mozilla/experimenter`.
    - When it comes to repository permissions, granting edit access to the [`@mozilla/project-nimbus`](https://github.com/orgs/mozilla/teams/project-nimbus/members) team seems like the easiest approach.
- You would not be able to merge changes to both documentation and the Experimenter codebase in the same Pull Request.

## Links

- [Existing issue discussion](https://github.com/mozilla/experimenter/issues/4758)
- [Monorepo with CircleCI Conditional Workflows](https://medium.com/labs42/monorepo-with-circleci-conditional-workflows-69e65d3f1bd0)
