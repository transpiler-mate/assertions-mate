# Tutorial: First Validated Workflow

This tutorial walks through a complete minimal setup using `assertions-mate` to validate workflow inputs before execution.

## Goal

By the end, you will:
- define assertion hints in a CWL workflow
- provide an inputs file
- run the CLI validator
- understand success and failure outputs

## Prerequisites

- Python 3.10+
- `assertions-mate` installed in your environment

## 1. Create a Minimal CWL Workflow

Create `workflow.cwl` with one integer input and three assertion hints:

```yaml
cwlVersion: v1.2
class: Workflow
id: sample
inputs:
  count:
    type: int
outputs: {}
steps: {}
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
      - id: positive-count
        cql2: "count > 0"
        message: "count must be greater than zero"
```

## 2. Create Valid Inputs

Create `inputs-valid.yaml`:

```yaml
count: 3
```

Run:

```bash
transpiler-mate assertions-mate --inputs inputs-valid.yaml workflow.cwl
```

Expected result: validators complete with no violations.

!!! Release note

    Since release **0.10.0**, `assertions-mate` is a transpiler-mate plugin.
    The standalone command was removed; use `transpiler-mate assertions-mate`.
    The Python library remains available.

## 3. Create Invalid Inputs

Create `inputs-invalid.yaml`:

```yaml
count: 42
```

Run:

```bash
transpiler-mate assertions-mate --inputs inputs-invalid.yaml workflow.cwl
```

Expected result: Rego rule violation (`count must be <= 10`).

## Next Steps

- Learn task-focused recipes in [How-to](../how-to/jsonschema.ipynb)
- Inspect contracts in [Reference](../reference/cli.md)
- Understand internals in [Explanation](../explanation/architecture.md)
