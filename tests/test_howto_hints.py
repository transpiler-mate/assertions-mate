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

from assertions_mate import (
    Cql2FilterHint,
    JSONSchemaHint,
    RegoPolicyHint,
    extract_assertion_hints,
)


class DummyWorkflow:
    """Provide CWL metadata and arbitrary hints for extraction tests."""

    def __init__(self, hints: list[object]) -> None:
        self.id = "file:///tmp/workflow.cwl#main"
        self.class_ = "Workflow"
        self.cwlVersion = "v1.2"
        self.hints = hints


def test_extract_assertion_hints_maps_multi_hint_workflow_from_howto() -> None:
    workflow = DummyWorkflow(
        hints=[
            {
                "class": "eoap:JSONSchemaHint",
                "json_schema": {
                    "type": "object",
                    "required": ["count"],
                    "properties": {"count": {"type": "integer", "minimum": 1}},
                },
            },
            {
                "class": "eoap:RegoPolicyHint",
                "module": """
                package workflow

                deny[msg] {
                  input["count"] > 10
                  msg := "count must be <= 10"
                }
                """,
                "queries": ["data.workflow.deny[_]"],
            },
            {
                "class": "eoap:Cql2FilterHint",
                "queries": [
                    {
                        "id": "rule-1",
                        "cql2": "count > 0",
                        "message": "count must be positive",
                    }
                ],
            },
        ]
    )

    hints = extract_assertion_hints(workflow)

    assert [type(hint) for hint in hints] == [JSONSchemaHint, RegoPolicyHint, Cql2FilterHint]


def test_extract_assertion_hints_maps_uri_host_rego_hint_from_howto() -> None:
    workflow = DummyWorkflow(
        hints=[
            {
                "class": "eoap:RegoPolicyHint",
                "module": """
                package workflow

                deny[msg] {
                  uri := input["input-uri"]
                  not startswith(uri, "https://")
                  msg := "input-uri must start with https://"
                }
                """,
                "queries": ["data.workflow.deny[_]"],
            }
        ]
    )

    hints = extract_assertion_hints(workflow)

    assert len(hints) == 1
    assert isinstance(hints[0], RegoPolicyHint)
