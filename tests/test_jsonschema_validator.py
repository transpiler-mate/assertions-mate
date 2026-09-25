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

from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest

from assertions_mate.jsonschema_validator import JSONSchemaRegistry, JSONSchemaValidator


def test_validate_inputs_returns_none_for_valid_payload() -> None:
    validator = JSONSchemaValidator(
        schema={
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
        }
    )

    result = validator.validate_inputs({"count": 3})

    assert result is None


def test_validate_inputs_returns_problem_details_for_invalid_payload() -> None:
    validator = JSONSchemaValidator(
        schema={
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
        }
    )

    result = validator.validate_inputs({})

    assert result is not None
    assert result.model_dump()["status"] == HTTPStatus.BAD_REQUEST
    assert result.errors is not None
    assert len(result.errors) == 1
    assert "required property" in result.errors[0].detail


@pytest.mark.parametrize(
    "payload, content_type",
    [
        (b'{"type": "object"}', "application/json"),
        (b"type: object", "application/yaml"),
        (b"type: object", "application/json"),
    ],
)
def test_load_schema_parses_json_yaml_and_mislabeled_yaml(
    payload: bytes, content_type: str
) -> None:
    registry = JSONSchemaRegistry()
    response = Mock(
        content=payload, status_code=HTTPStatus.OK, headers={"Content-Type": content_type}
    )
    with patch.object(registry.session, "get", return_value=response):
        assert registry.load_schema("https://example.com/schema") == {"type": "object"}


@pytest.mark.parametrize("content_type", ["application/json", "application/yaml"])
def test_load_schema_reports_failure_when_both_parsers_reject_document(content_type: str) -> None:
    registry = JSONSchemaRegistry()
    response = Mock(content=b"{", status_code=HTTPStatus.OK, headers={"Content-Type": content_type})
    with (
        patch.object(registry.session, "get", return_value=response),
        pytest.raises(ValueError, match="Unable to parse JSON Schema") as caught,
    ):
        registry.load_schema("https://example.com/schema")
    assert caught.value.__cause__ is not None
