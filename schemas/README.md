# Nimbus Schemas

This directory contains a published package of schemas used by different parts of the Mozilla Nimbus experimentation ecosystem.

## Installation/Usage
### Prerequisites
- python ^3.10
- poetry ^1.2.2

From project root (i.e., parent to this directory)
- Install: `make schemas_install`
- Run linting and tests: `make schemas_check`
- Code formatting: `make schemas_code_format`

## Schemas
### Jetstream

Contains schemas describing analysis results, metadata, and errors from [Jetstream](https://github.com/mozilla/jetstream).
