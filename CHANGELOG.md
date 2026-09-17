# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Deprecated

### Removed

### Fixed

## [0.9.0] - 2026-07-31

### Added

- Stronger code chekers with Ruff+McCabe & Bandit

### Changed

- dependencies bump:
  - `click` to `8.4.2`.
  - `cwl-utils` to `0.42`.
  - `cwl2ogc` to `0.19.0`.
  - `pygeofilter[backend-native]` to `0.4.0`.
  - `requests` to `2.34.2`.
  - `session-adapters` to `0.5.0`.
  - `eoap-problems-registry` to `1.3.0`.

- `click` dependency moved to `optional-dependencies`

### Removed

- `PyYAML` replaced by `ruamel.yaml` already used by `cwl-utils`. 

## [0.8.0] - 2026-07-21

### Changed

- `eoap-problems-registry` dependency version bump.

## [0.7.0] - 2026-07-20

### Changed

- Custom `error_models` replaced by [eoap-problems-registry](https://pypi.org/project/eoap-problems-registry/)

### Fixed

- `Cql2Query#cql2` definition in schema must reflect `Any` since can assume also a `Mapping` value.
- Fixed `Cql2Query#id` definition in schema of `JSON-LD`.
- Disambiguation of `Cql2FilterHint#queries` and `RegoPolicyHint#queries` in schema.

### Security

## [0.6.0] - 2026-10-06

### Fixed

- Unresolvable $ref entities in JSON Schema

## [0.5.0] - 2026-08-06

### Changed

- Audit pyproject dependencies

## [0.4.0] - 2026-05-29

### Added

- Expanded the documentation site with Diataxis-oriented tutorials, how-to guides, reference pages, and explanation pages.
- Added runnable CWL examples for URI, datetime, date range, polygon, bbox overlap, CQL2 JSON, enum, array cardinality, multi-hint, Rego, and pytest-based validation workflows.
- Added generated schema reference documentation for assertion hints.
- Added support for `Cql2FilterHint.custom_functions`, allowing CWL hints to provide Python functions used by CQL2 validation.
- Added tests that exercise how-to hint extraction and CQL2 custom function execution.

### Changed

- Changed assertion schema records to extend `cwl:ProcessRequirement` instead of `cwl:ProcessHint`.
- Updated the CQL2 hint schema with field documentation and links to CQL2 and Rego references.
- Moved the default Taskfile workflow to remote shared quality tasks and added documentation/schema-generation tasks.
- Updated package metadata through `0.4.0`; the repository currently has no Git tags after `v0.2.0`.

### Fixed

- Normalized CWL/YAML scalar values before parsing CQL2 JSON filters.
- Updated Rego validation to use the default regopy interpreter setup, avoiding runtime issues with supported policy syntax.
- Fixed URI and datetime examples to validate typed input payloads through their `value` fields.
- Fixed and expanded CQL2 bbox validation examples to use custom functions declared in the CWL hint.
- Fixed MkDocs configuration and documentation navigation for the expanded site.

## [0.2.0] - 2026-03-06

### Added

- Added the initial Python package for validating CWL workflow inputs from embedded assertion hints.
- Added support for `eoap:JSONSchemaHint`, `eoap:RegoPolicyHint`, and `eoap:Cql2FilterHint`.
- Added the `assertions-mate` command-line entry point for loading CWL workflows, reading YAML inputs, and reporting validation violations.
- Added CWL schema definitions for the supported assertion hint records.
- Added Pydantic error models for validation problem details and business rule violations.
- Added unit tests for JSON Schema, Rego, CQL2, and hint extraction behavior.
- Added README usage documentation, notebooks, and the initial MkDocs documentation setup.
- Added Hatch, pytest, Ruff, Taskfile, and CI configuration for development and validation workflows.
- Added Apache-2.0 license headers across the package.

### Changed

- Updated workflow CI to use Python 3.12 and then expanded the test matrix across Python 3.10 through 3.14.
- Aligned hint keyword naming and schema structure with CWL/EOAP conventions.

### Fixed

- Fixed documentation build issues around PlantUML and MkDocs plugin configuration.
- Fixed API documentation generation and schema behavior according to canonical CWL practices.

[Unreleased]: https://github.com/Terradue/assertions-mate/compare/v0.9.0...develop
[0.9.0]: https://github.com/Terradue/assertions-mate/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/Terradue/assertions-mate/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/Terradue/assertions-mate/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/Terradue/assertions-mate/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/Terradue/assertions-mate/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Terradue/assertions-mate/compare/v0.2.0...v0.4.0
[0.2.0]: https://github.com/Terradue/assertions-mate/releases/tag/v0.2.0
