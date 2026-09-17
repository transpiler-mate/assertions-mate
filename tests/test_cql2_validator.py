# Copyright 2025 Terradue
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
from types import SimpleNamespace

import pytest
from cwl_utils.parser import load_document_by_uri
from ruamel.yaml import YAML
from transpiler_mate.api import PluginFailureError

from assertions_mate import Cql2FilterHint, Cql2Query, extract_assertion_hints
from assertions_mate.cql2_validator import Cql2EvaluationError, Cql2Validator
from assertions_mate.plugin import _scan_workflow


def test_validate_inputs_reports_business_rule_violation_when_predicate_fails():
    validator = Cql2Validator(
        queries=[
            Cql2Query(
                id="rule-1",
                cql2="count > 5",
                message="Count must be greater than 5",
            )
        ]
    )

    result = validator.validate_inputs({"count": 2})

    assert result is not None
    assert result.status == 422
    assert result.errors is not None
    assert len(result.errors) == 1
    assert result.errors[0].pointer == "rule-1"
    assert result.errors[0].detail == "Count must be greater than 5"


def test_validate_inputs_reports_unrecognized_filter_format():
    validator = Cql2Validator(
        queries=[
            Cql2Query.model_construct(
                id="rule-2",
                cql2=5,
                message="should not be used",
            )
        ]
    )

    result = validator.validate_inputs({"count": 2})

    assert result is not None
    assert result.errors is not None
    assert len(result.errors) == 1
    assert result.errors[0].pointer == "rule-2"
    assert "unrecognizible format" in result.errors[0].detail


def test_validate_inputs_executes_ensure_bbox_custom_function_from_cwl_hint():
    example_dir = (
        Path(__file__).resolve().parents[1] / "examples" / "bbox-overlap-validation"
    )
    workflow = load_document_by_uri(
        path=example_dir / "workflow.cwl",
        load_all=True,
    )
    if isinstance(workflow, list):
        workflow = workflow[0]
    hints = [
        hint
        for hint in extract_assertion_hints(workflow)
        if isinstance(hint, Cql2FilterHint)
    ]

    assert len(hints) == 1
    assert hints[0].custom_functions is not None
    assert "ensure_bbox" in hints[0].custom_functions

    validator = hints[0].validator()

    yaml = YAML()

    with (example_dir / "inputs-valid.yaml").open(encoding="utf-8") as input_stream:
        valid_inputs = yaml.load(input_stream)

    with (example_dir / "inputs-invalid.yaml").open(encoding="utf-8") as input_stream:
        invalid_inputs = yaml.load(input_stream)

    assert validator.validate_inputs(valid_inputs) is None

    result = validator.validate_inputs(invalid_inputs)

    assert result is not None
    assert result.status == 422
    assert result.errors is not None
    assert len(result.errors) == 1
    assert result.errors[0].pointer == "bbox-overlap"
    assert result.errors[0].detail == "bbox_1 must overlap bbox_2"


@pytest.mark.parametrize("data", [{}, {"aoi": None}])
def test_polygon_missing_aoi_reports_only_presence_violation(data):
    path = (
        Path(__file__).resolve().parents[1] / "examples/polygon-validation/workflow.cwl"
    )
    workflow = YAML().load(path)["$graph"][0]
    hint = Cql2FilterHint(**workflow["hints"][0])

    result = hint.validator().validate_inputs(data)

    assert result is not None
    assert [(error.pointer, error.detail) for error in result.errors] == [
        ("aoi-present", "aoi must be provided")
    ]


@pytest.mark.parametrize(
    "data, expected",
    [
        ({"aoi": {"type": "Polygon", "bbox": [0, 0, 1, 1]}}, []),
        (
            {"aoi": {"type": "Point", "bbox": [0, 0, 1, 1]}},
            ["aoi.type must be Polygon"],
        ),
        ({"aoi": {"type": "Polygon"}}, ["aoi.bbox must be provided"]),
    ],
)
def test_polygon_non_null_rules_still_validate(data, expected):
    path = (
        Path(__file__).resolve().parents[1] / "examples/polygon-validation/workflow.cwl"
    )
    hint = Cql2FilterHint(**YAML().load(path)["$graph"][0]["hints"][0])

    result = hint.validator().validate_inputs(data)

    assert ([error.detail for error in result.errors] if result else []) == expected


def test_custom_function_failure_is_not_a_business_rule_violation():
    validator = Cql2Validator(
        queries=[
            Cql2Query(
                id="broken-rule", cql2="broken(count) = 1", message="Invalid count"
            )
        ],
        custom_functions="def broken(value):\n    raise ValueError('internal detail')",
    )

    with pytest.raises(Cql2EvaluationError) as caught:
        validator.validate_inputs({"count": 1})

    assert str(caught.value) == "Could not evaluate rule 'broken-rule'"
    assert isinstance(caught.value.__cause__, ValueError)


def test_plugin_reports_evaluation_failure_without_success():
    workflow = SimpleNamespace(
        id="file:///tmp/workflow.cwl#main",
        class_="Workflow",
        cwlVersion="v1.2",
        hints=[
            {
                "class": "eoap:Cql2FilterHint",
                "queries": [
                    {
                        "id": "broken-rule",
                        "cql2": "aoi.type = 'Polygon'",
                        "message": "Invalid AOI",
                    }
                ],
            }
        ],
    )

    with pytest.raises(
        PluginFailureError, match="Could not evaluate rule 'broken-rule'"
    ):
        _scan_workflow(workflow, {"aoi": None})
