# Use Docusaurus + GH Pages for the Nimbus User Doc Hub

- Deciders: Lauren Zugai, Kate Hudson, and Jody Heavener, with additional input from those involved in Nimbus
- Date: 2021-02-25

Technical Story: [Documentation Hub for Nimbus Users](https://jira.mozilla.com/browse/EXP-860)

## Context and Problem Statement

In scaling Nimbus for 2021 and beyond, we need to provide experiment owners, data scientists, and desktop and Fenix engineers documentation to better streamline working with the platform. Following the same line of thought in [`nimbus-shared` ADR 0001](https://github.com/mozilla/nimbus-shared/blob/main/docs/adr/0001-one-console-app.md), users should expect a single source of truth for their documentation needs.

The documentation that will be part of the hub includes:

- A new front-page or home-page doc, likely written in MD, with a brief overview of Nimbus and instructions for users on the workflow for doc maintenance
- New docs, likely written in MD, and depending on the chosen option, possibly optionally with React components (if Docusaurus or Storybook) or custom JS (if Docusaurus, Storybook, or `mdBook`)
  - For Fenix engineers: SDK docs for integration in Fenix
  - For experiment owners: How to use the console, either living here or in Mana
  - For data scientists: How to add Jetstream configs
  - How to read automated analysis, either living here or in Mana
  - In the future, iOS and Gecko integration docs
- Existing docs
  - For Desktop engineers: [SDK docs for integration in desktop front end](https://www.notion.so/k88hudson/Nimbus-Migration-Guide-for-Desktop-Front-End-Experiments-d36c21e505f84550aad1202897fc4ba3)
- Various Google docs and Mana links
- Possibly existing MD docs living in other repos

## Decision Drivers

- Docs should be kept in a central location and cross-linking should be easy
- Finding relevant documentation should be painless, quick, and clear for all of our users, and cover their specific doc needs, like copying a code snippet in various languages
- Docs should be easily editable by anyone; maintenance and workflow should be straightforward and scalability should be taken into account
- Set up, hosting, and deployment efforts should be minimal

## Considered Options

- Mana / Confluence
- Docusaurus + GH Pages
- Experimenter repo Wiki
- Storybook
- mdBook + GH Pages

## Decision Outcome

Chosen option: "Docusaurus + GH pages", because Docusaurus provides a flexible and easily/automatically updated sidebar, allows MD and custom JS when needed, and provides a robust search bar. To minimize maintenance efforts, customization will be kept to a minimum and MD files can be edited directly in the GH UI. GitHub Pages takes care of deployment efforts and we can make the URL memorable with a custom domain if we wish to.

The top three choices based on discussions held in the PR for this ADR were Docusaurus, the Experimenter repo Wiki, and `mdBook`. Docusaurus was chosen over the Experimenter repo Wiki because a repo Wiki would not allow custom JS, it's less scalable, and more difficult to search. Docusaurus was chosen over `mdBook` because `mdBook` does not allow external links in the sidebar and requires a separate file edited for sidebar updates which would add one more step to the maintenance workflow.

## Pros and Cons of the Options

### Mana

With this option, we would create a "Documentation" child page [on Mana](https://mana.mozilla.org/wiki/display/FJT/Project+Nimbus) with a home page with a quick explanation of the Nimbus platform, linking out to relevant high-level docs, and creating individual pages for "User docs" (product managers, experiment owners), "Engineering docs," and "Data docs." May warrant some shuffling of other pages.

Pros

- A lot of documentation already exists on Mana and may be the most natural place for experiment owners to look for central docs; would be easily accessible and editable
- An email is sent out to those subscribed when anyone updates a document
- Some non-engineer users may feel the most comfortable editing and maintaining in Mana rather than editing in GH or submitting a PR, and users can see their changes instantaneously
- No set up or deployment required

Neutral

- Documentation edits wouldn't require peer review and approval
- Has a search option, but within Firefox Journey and not within Nimbus specifically
- Jira tickets can be easily linked by reference number and other links can be dropped in where needed, but there doesn't appear to be an option to link to external links via the sidebar

Cons

- Does not appear to be a natural place to look and maintain for engineers
- [Supports Markdown](https://confluence.atlassian.com/doc/confluence-wiki-markup-251003035.html#ConfluenceWikiMarkup-markdownCanIinsertmarkdown?), but differs slightly from conventional Markdown and won't load separate files, and seems clunky
- Can be hard to read as the text expands across the entire page
- Is not very flexible or customizable without paid add-ons
- Doesn't integrate well with generated docs
- Multi-language code examples would be flat, take up more screen space, and visually not look as ideal as they could with a more flexible option like Docusaurus or Storybook
- Is arguably the least open-source friendly

**Workflow for this option**

No set up required. Doc maintainers will go to Mana and make their edits on the relevant page(s).

### Docusaurus + GH Pages

The [FxA Ecosystem Platform docs](https://mozilla.github.io/ecosystem-platform/) use [Docusaurus](https://docusaurus.io/). For this option, we would likely set up a `docs` or similar branch specifically for documentation in the Experimenter repo and we would point GH to push this branch to [GitHub pages](https://docs.github.com/en/github/working-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

Pros

- Has a search bar that appears to be robust
- Would provide a flexible set up - external MD files can be automatically pulled into the sidebar based on name, and [React components](https://v2.docusaurus.io/docs/creating-pages#add-a-react-page) or JS can be used to create pages. [Supports MDX](https://v2.docusaurus.io/docs/markdown-features#embedding-react-components-with-mdx). It may be handy to create UI components for certain pieces of documentation, like clicking a tab to choose a language and click to copy various code snippets
- The site navigation is also flexible. [External links](https://docusaurus.io/docs/en/navigation#adding-external-links) can be displayed in the navigation for docs that live somewhere else but should be linked at a higher level
- This package was made for open source documentation and has [various plugins](https://v2.docusaurus.io/docs/api/plugins) available, though many less than Storybook
- Deployment would be handled by GitHub Pages, and GH Pages allows custom domains, if we later want to use a nicer URL

Neutral:

- Documentation edits would require a PR and approval in the Experimenter repo, and notifications for approval (and for awareness) could be subscribed to with a tool like [`issue-label-notifier`](https://github.com/marketplace/actions/issue-label-notifier)
- Could be considered overkill for Nimbus Doc Hub needs, but would also set us up for scalability
- Docusaurus does not have as much documentation as other options, but it should be adequate for our needs, and we can reference the FxA Ecosystem Platform to get started

Cons

- Requires some, albeit not a lot, of setup, including ensuring doc PRs don't trigger CI and incur unnecessary costs
- Some doc maintainers don't prefer checking into code and using GH¹; however, if it's only Markdown files that need editing, they can can be edited in GitHub directly without checking into code
- To preview sidebar / other changes manually if the user desires, the user will need to check into the branch and run a build command
- May pose a small learning curve for the team¹

**Workflow for this option**

Requires around `8` story points to set up. Doc maintainers will go into GitHub to edit/add Markdown files, follow the GitHub UI to place a pull request into `Experimenter` after they've finished, and add a label for `issue-label-notifier` to pick up. They can alternatively check into the code to make edits, but they must check into the code to do anything more complex than add or edit MD files.

A demo should likely be made to help ease the process for maintainers.

### Experimenter repo Wiki

[Wiki pages](https://docs.github.com/en/github/building-a-strong-community/adding-or-editing-wiki-pages) are made for GitHub repository project documentation purposes. For this option, the doc hub would reside at the [Experimenter Wiki](https://github.com/mozilla/experimenter/wiki).

Pros

- Easily accessible via the "Wiki" tab in the Experimenter repo
- Supports a variety of "edit" modes, including Markdown, with format helpers
- Doc updates wouldn't require checking into code (though, neither would MarkDown file edits that can be done in GitHub directly), and users can see their changes instantaneously and correct mistakes without a subsequent PR
- [Change history](https://docs.github.com/en/github/building-a-strong-community/viewing-a-wikis-history-of-changes) is not lost
- No setup or deployment required
- [pro/neutral] Has a customizable navigational sidebar that allows external links, but not ones that open in a new tab (can be noted with `↗`)
- [pro/neutral] Has search functionality, though in the Wiki, only searches for page titles. Searching in the body can be done [in the main GH searchbar](https://github.com/mozilla/experimenter/search?q=testing+123+in%3Abody&type=wikis) with options specified

Neutral

- Documentation edits wouldn't require peer review and approval
- It appears we could receive edit notifications via [Slack Notify](https://github.com/marketplace/actions/slack-notify), a third-party Slack integration, to listen for the [gollum](https://docs.github.com/en/actions/reference/events-that-trigger-workflows#gollum) event. The standard GitHub Slack App has [pending notification support](https://github.com/integrations/slack/pull/946). Though, this is untested, requires a small amount of setup, and may not be a preferred way to receive notifications

Cons

- Repo Wikis are not as flexible as Docusaurus or Storybook
  - Multi-language code examples would be flat, take up more screen space, and visually not look as ideal as they could with a more flexible option like Docusaurus or Storybook
- Doesn't integrate well with generated docs
- Some doc maintainers don't prefer using GH¹

**Workflow for this option**

No set up required. Doc maintainers will go to the Experimenter Wiki page and make their edits on the relevant page(s) and edit the sidebar accordingly. External links can be denoted with `↗` and subpages can be denoted with `—` (specifics can be decided later if this is the chosen option).

### Storybook

[Storybook](https://github.com/storybookjs/storybook) is a versatile package that can not only be used to aid in UI development, but can also be used for various kinds of guides and documentation.

We currently use Storybook in [`nimbus-ui`](https://github.com/mozilla/experimenter/tree/main/app/experimenter/nimbus-ui), which at the time of writing has a small documentation section, and builds are automatically deployed to [`mozilla-storybooks-experimenter`](https://storage.googleapis.com/mozilla-storybooks-experimenter/index.html) per commit.

Pros

- Would provide a flexible set up - documentation can be written in Markdown, in JS or in external files, with a package or add-on to parse and display markdown, like [`react-markdown`](https://github.com/remarkjs/react-markdown) or [`storybook-readme`](https://github.com/tuchk4/storybook-readme). It may be handy to create UI components for certain pieces of documentation, like clicking a tab to choose a language and click to copy various code snippets
- At least one major documentation maintainer has experience with Storybook
- Storybook has a lot of [addons](https://storybook.js.org/addons) available
- We already have automatic deployment setup

Neutral:

- Documentation edits would require a PR and approval in the Experimenter repo, and notifications for approval (and for awareness) could be subscribed to with a tool like [issue-label-notifier](https://github.com/marketplace/actions/issue-label-notifier)
- Could be considered overkill for Nimbus Doc Hub needs, but would also set us up for flexible scalability
- The URL would be easily accessible, though it may take a couple of clicks to pull up the latest unless our deployment tool is tweaked

Cons

- Requires some, albeit not a lot, of setup
- Has a search option, but it is not as robust for documentation searching as some other options
- While Docusaurus can automatically pull in MD files, Storybook would still require a corresponding JSX/JS file to pull in and display the file unless we built a tool for this
- Does not appear to have an external link-out option for navigation links
- Some doc maintainers don't prefer checking into code and using GH¹
- May pose a learning curve for those unfamiliar with Storybook, and out of all of our options, is arguably the most involved¹

**Workflow for this option**

Requires around `5` story points to set up, but more if other tools should be created for it. Doc maintainers could directly edit MD files in GitHub, but if a new page is needed, a corresponding JS/JSX file may be needed to display it in unless effort was put into a tool. Storybook more than any other option would ask maintainers to check into the code. Whether directly in GitHub or on the doc maintainer's machine, changes would be placed a pull request into Experimenter with a label for issue-label-notifier to pick up.

A demo should likely be made to help ease the process for maintainers.

#### mdBook + GH Pages

[`mdBook`](https://github.com/rust-lang/mdBook) is a tool that generates book-like documentation from Markdown files. For this option, we would likely set up a `docs` or similar branch specifically for documentation in the Experimenter repo and we would point GH to push this branch to [GitHub pages](https://docs.github.com/en/github/working-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

Pros:

- Has a search bar that appears to be robust
- Is used extensively by [Glean](https://docs.telemetry.mozilla.org/concepts/glean/glean.html) and is written in Rust
- Supports adding JS snippets which would allow for clicking a tab to choose a language and click to copy various code snippets, [see this done in Glean docs](https://mozilla.github.io/glean/book/user/metrics/boolean.html)
- Deployment would be handled by GitHub Pages, and GH Pages allows custom domains, if we later want to use a nicer URL

Neutral:

- Has a flexible site navigation in title links and sublinks, but does not support external links in the sidebar, though there is [an open issue](https://github.com/rust-lang/mdBook/issues/919) for the feature
- Documentation edits would require a PR and approval in the Experimenter repo, and notifications for approval (and for awareness) could be subscribed to with a tool like [`issue-label-notifier`](https://github.com/marketplace/actions/issue-label-notifier)
- While Docusaurus pulls in external MD files and builds the sidebar automatically (optionally customizable), `mdBook` requires an edit in the [`SUMMARY.MD`](https://rust-lang.github.io/mdBook/format/summary.html) file as well to reflect sidebar updates
- This package was made for open source documentation, but does not appear to have plugins or add-ons

Cons:

- Requires some, albeit not a lot, of setup
- Does not support external links in the sidebar, though there is [an open issue](https://github.com/rust-lang/mdBook/issues/919) for the feature
- Is not as flexible as Docusaurus or Storybook and only allows MD files
- Is much less popular than Docusaurus, in terms of GH stars and downloads
- To preview sidebar / other changes manually if the user desires, the user will need to check into the branch and run a build command
- Some doc maintainers don't prefer using GH¹

**Workflow for this option**

Requires around `5` story points to set up, perhaps `8` for an initial build out and importing custom JS. Doc maintainers will go into GitHub to edit/add Markdown files including `SUMMARY.MD` if the sidebar needs to be updated, follow the GitHub UI to place a pull request into `Experimenter` after they've finished, and add a label for `issue-label-notifier` to pick up.

---

¹These points can be partially alleviated with clear "how to" documentation.

## Links

- [Nimbus Mana](https://mana.mozilla.org/wiki/display/FJT/Project+Nimbus)
- [Experimenter repo](https://github.com/mozilla/experimenter/) / [`nimbus-ui` Storybook deployment page](https://storage.googleapis.com/mozilla-storybooks-experimenter/index.html) / [Wiki](https://github.com/mozilla/experimenter/wiki)
- [Docusaurus](https://docusaurus.io/) / [FxA Ecosystem Platform docs](https://mozilla.github.io/ecosystem-platform/)
- [mdBook](https://github.com/rust-lang/mdBook)
- Also see the [FxA Settings Design Guide](https://storage.googleapis.com/mozilla-storybooks-fxa/index.html) (click on the latest commit from `main`), written in Storybook
