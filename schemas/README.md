# Nimbus Schemas

This directory contains a package of schemas published to various repositories for use by different parts of the Mozilla Nimbus experimentation ecosystem.


## Installation/Usage
### Prerequisites
- python ^3.10
- poetry ^1.8.4
- node ^16
- yarn ^1.22

### Common Operations
From project root (i.e., parent to this directory)
- Build: `make schemas_build`
- Run linting and tests: `make schemas_check`
- Code formatting: `make schemas_format`


### Adding New Schemas

**Example**
Creating a new sub-package `new_stuff`
1. Add new directory `mozilla_nimbus_schemas` / `new_stuff` with schemas inside.
1. Add `new_stuff` schemas to the `new_stuff` directory's `__init__.py` file.
1. Add `new_stuff` to top level `__init__.py`:
    >`from mozilla_nimbus_schemas.new_stuff import *`
1. Generate Typescript and/or JSON Schemas for `new_stuff` by updating the `generate_json_schema.py` script like so:
    
    a. Import `new_stuff` alongside existing `mozilla_nimbus_schemas` imports, e.g.,
      >`from mozilla_nimbus_schemas import experiments, jetstream, new_stuff`
  
    b. (optional) Add `new_stuff` to Typescript generation
    * Update `TS_SCHEMA_PACKAGES` list, e.g.,
      >`TS_SCHEMA_PACKAGES = [experiments, jetstream, new_stuff]`

    c. (optional) Add `new_stuff` to JSON Schema generation
    * Update `JSON_SCHEMA_PACKAGES` list, e.g.,
      >`JSON_SCHEMA_PACKAGES = [experiments, new_stuff]`

1. Build everything with `make schemas_build`

1. Update the version (see [Versioning](#versioningversioning) below).

## Schemas
### Jetstream

Contains schemas describing analysis results, metadata, and errors from [Jetstream](https://github.com/mozilla/jetstream).

### Experiments

Defines the schemas used for validating the Experimenter v6 API. Previously defined in the now-deprecated [`nimbus-shared`](https://github.com/mozilla/nimbus-shared).


## Deployment
The build and deployment occurs automatically through CI. A deployment is triggered on merges into the `main` branch when the version number changes. Schemas are published to various repos for access in different languages.

### Versioning
`mozilla-nimbus-schemas` uses semantic versioning (`semver`) of `major.minor.patch`. Previously, we
used a date-based versioning scheme (`CalVer`), which is why the version is so high (3000+). Any
breaking changes should result in an increase in the major version.

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
