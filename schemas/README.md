# Nimbus Schemas

This directory contains a package of schemas published to various repositories for use by different parts of the Mozilla Nimbus experimentation ecosystem.


## Installation/Usage
### Prerequisites
- python ^3.10
- poetry ^1.8.4
- node ^16
- yarn ^1.22

#### Common Operations
From project root (i.e., parent to this directory)
- Build: `make schemas_build`
- Run linting and tests: `make schemas_check`
- Code formatting: `make schemas_format`

#### Building Python Schemas Package
`make schemas_build_pypi`

#### Building Typescript Schemas Package
`make schemas_build_npm`

## Schemas
### Jetstream

Contains schemas describing analysis results, metadata, and errors from [Jetstream](https://github.com/mozilla/jetstream).


## Deployment
The build and deployment occurs automatically through CI. A deployment is triggered on merges into the `main` branch when the version number changes. Schemas are published to various repos for access in different languages.

#### Versioning
`mozilla-nimbus-schemas` uses a date-based versioning scheme (`CalVer`). The format is `yyyy.m.MINOR`, where `m` is the non-zero-padded month, and `MINOR` is an incrementing number starting from 1 for each month. Notably, this `MINOR` number does NOT correspond to the day of the month. For example, the second release in June of 2023 would have a version of `2023.6.2`.

#### Version Updates
1. To update the published package versions, update the `VERSION` file in this directory.
  - From the project root, you can run the helper script:
    - `./scripts/set_schemas_version.sh <version>`
  - Or write to the file:
    - `echo <version> > ./schemas/VERSION`
  - Or simply edit the file in any text editor.
2. Update the package versions with the new VERSION file:
  - `make schemas_version`

### Python
Published to PyPI as `mozilla-nimbus-schemas`

### Typescript
Published to NPM as `@mozilla/nimbus-schemas`

### Rust
Not yet implemented.
