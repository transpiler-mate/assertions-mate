# Assertions Mate

[![PyPI - Version](https://img.shields.io/pypi/v/assertions-mate.svg)](https://pypi.org/project/assertions-mate)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/assertions-mate.svg)](https://pypi.org/project/assertions-mate)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/transpiler-mate/assertions-mate/package.yaml?branch=develop&event=push&label=build&logo=githubactions)](https://github.com/transpiler-mate/assertions-mate/actions/workflows/package.yaml?query=branch%3Adevelop)
[![Code coverage](https://img.shields.io/codecov/c/github/transpiler-mate/assertions-mate/develop?logo=codecov)](https://app.codecov.io/gh/transpiler-mate/assertions-mate/tree/develop)

`assertions-mate` validates CWL workflow inputs against assertion hints embedded in the workflow definition.

It adds policy and rule checks on top of CWL typing by supporting:
- JSON Schema validation
- Rego policy validation (OPA)
- CQL2 expression validation

Documentation site: https://terradue.github.io/assertions-mate/

Documentation follows the Diataxis framework:
- Tutorials: learning-oriented walkthroughs
- How-to guides: task-focused recipes
- Reference: technical contracts and interfaces
- Explanation: design rationale and concepts

## Why Use It

When a CWL workflow needs stricter runtime checks (business rules, policy constraints, geospatial conditions), `assertions-mate` lets you define them as workflow hints and evaluate them against an input payload before execution.

## Installation

### From source (recommended for development)

```bash
git clone https://github.com/Terradue/assertions-mate.git
cd assertions-mate
pip install -e .
```

### Runtime requirements

- Python `>= 3.10`
- Dependencies are managed in `pyproject.toml`

## Command Line Usage

> [!NOTE]
> Since release **0.10.0**, `assertions-mate` is a transpiler-mate plugin.
> The standalone command was removed; use `transpiler-mate assertions-mate`.
> The Python library remains available.

```bash
pip install transpiler-mate-runtime "assertions-mate>=0.10.0"
```

After installation, run:

```bash
transpiler-mate assertions-mate --inputs path/to/inputs.yaml path/to/workflow.cwl
```

What happens:
1. The CWL document is loaded.
2. Assertion hints are discovered from `workflow.hints`.
3. Matching validators are built and executed against the input mapping.
4. Validation issues are reported with pointer and detail messages.

## Supported Assertion Hints

The tool maps `eoap:` hint classes to internal validators:

- `eoap:JSONSchemaHint`
- `eoap:RegoPolicyHint`
- `eoap:Cql2FilterHint`

### Example `hints` snippet

```yaml
hints:
  - class: eoap:JSONSchemaHint
    json_schema:
      type: object
      required: [count]
      properties:
        count:
          type: integer
          minimum: 1

  - class: eoap:RegoPolicyHint
    module: |
      package workflow
      deny contains "count must be <= 10" if {
        input.count > 10
      }
    queries:
      - data.workflow.deny[_]

  - class: eoap:Cql2FilterHint
    queries:
      - id: cql-rule-1
        cql2: "count > 0"
        message: "count must be greater than zero"
```

## Development

This project uses Hatch environments and pytest.

```bash
# Run tests
hatch run test:test-q

# Run formatting check
hatch run dev:lint

# Run lint checks with fixes
hatch run dev:check
```

If you use Taskfile:

```bash
task test
task lint
task check
```

## Project Layout

- `src/assertions_mate/` core package and CLI
- `tests/` unit tests
- `schemas/` CWL hint schema definitions
- `docs/` notebooks and documentation sources

## License

[![Apache License, Version 2.0](https://img.shields.io/badge/license-Apache%20License%202.0-blue)](https://www.apache.org/licenses/LICENSE-2.0)
