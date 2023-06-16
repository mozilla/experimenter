# Nimbus Schemas

This directory contains a published package of schemas used by different parts of the Mozilla Nimbus experimentation ecosystem.

## Versioning
`mozilla-nimbus-schemas` uses a date-based versioning scheme. The format is `yyyy.m.#`, where `m` is the non-zero-padded month, and `#` is an incrementing number starting from 1 for each month. For example, the second release in June of 2023 would have a version of `2023.6.2`.

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
