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

import pytest
from ruamel.yaml import YAML

from assertions_mate.rego_validator import RegoValidator


EXAMPLE_DIR = Path(__file__).resolve().parents[1] / "examples/required-property-validation"


@pytest.fixture
def validator():
    workflow = YAML().load(EXAMPLE_DIR / "workflow.cwl")
    hint = workflow["$graph"][0]["hints"][0]
    return RegoValidator(module=hint["module"], queries=hint["queries"])


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"aoi": None},
        {"aoi": {}},
        {"aoi": {"properties": None}},
        {"aoi": {"properties": {}}},
        {"aoi": {"properties": {"name": None}}},
    ],
)
def test_missing_or_null_name_is_rejected(validator, data):
    result = validator.validate_inputs(data)

    assert result is not None
    assert any(
        "aoi.properties.name must be provided" in error.detail
        for error in result.errors
    )


@pytest.mark.parametrize("name", ["my-aoi", "", False, 0])
def test_present_non_null_name_is_accepted(validator, name):
    # This rule checks presence, not the value's type or truthiness.
    assert validator.validate_inputs({"aoi": {"properties": {"name": name}}}) is None


@pytest.mark.parametrize("kind, rejected", [("valid", False), ("invalid", True)])
def test_example_fixtures(validator, kind, rejected):
    data = YAML().load(EXAMPLE_DIR / f"inputs-{kind}.yaml")

    assert (validator.validate_inputs(data) is not None) == rejected
