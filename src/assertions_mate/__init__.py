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

"""CWL assertion hint models and the shared input validation interface.

Hints configure JSON Schema, Rego, or CQL2 validators and serialize to
annotation payloads. Use `extract_assertion_hints` to read them from a
parsed CWL process.
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from cwl2ogc import BaseCWLtypes2OGCConverter  # type: ignore[import-untyped]
from eoap_problems_registry import ProblemDetails
from loguru import logger
from pydantic import BaseModel, computed_field, model_serializer


class BaseValidator(ABC):
    """Interface for validators that check a mapping of workflow inputs."""

    @abstractmethod
    def validate_inputs(self, data: Mapping[str, Any]) -> ProblemDetails | None:
        """Check workflow inputs against the configured assertions.

        Args:
            data: Workflow input names mapped to their values.

        Returns:
            Problem details describing violations, or None when validation succeeds.

        Implementations may raise an exception when validation cannot be performed.
        """
        pass


class AssertionHint(BaseModel):
    """Base model for an assertion hint attached to a CWL process.

    Attributes:
        parent_workflow: Parsed CWL process containing the hint, when available.
    """

    parent_workflow: Any | None = None

    @property
    @computed_field
    @abstractmethod
    def annotation(self) -> str:
        """Return the annotation key used to identify this hint."""
        pass

    @abstractmethod
    def validator(self) -> BaseValidator:
        """Create a validator configured from this hint."""
        pass


class JSONSchemaHint(AssertionHint):
    """Configure JSON Schema validation of workflow inputs.

    Attributes:
        json_schema: Explicit schema to apply, including an explicitly empty schema.
            When omitted, derive a schema from parent_workflow if available;
            otherwise use an empty schema.
    """

    json_schema: Mapping[str, Any] = {}

    @staticmethod
    def get_annotation_name() -> str:
        """Return the annotation key for JSON Schema input constraints."""
        return "eoap.ogc.org/inputs-json-schema"

    @property
    def annotation(self) -> str:
        """Return the annotation key for JSON Schema input constraints."""
        return JSONSchemaHint.get_annotation_name()

    def _get_schema(self) -> Mapping[str, Any]:
        """Return the explicit schema, or derive it from the parent CWL process."""
        if "json_schema" in self.model_fields_set or self.parent_workflow is None:
            return self.json_schema
        schema = BaseCWLtypes2OGCConverter(self.parent_workflow).get_inputs_json_schema()
        if not isinstance(schema, Mapping):
            raise TypeError("The CWL converter must return a JSON Schema mapping")
        return schema

    @model_serializer
    def ser_model(self) -> Mapping[str, Any]:
        """Serialize the hint as its effective JSON Schema document."""
        return self._get_schema()

    def validator(self) -> BaseValidator:
        """Create a JSON Schema validator using the effective schema."""
        from .jsonschema_validator import JSONSchemaValidator

        return JSONSchemaValidator(schema=self._get_schema())


class RegoPolicyHint(AssertionHint):
    """Configure Rego policy queries for workflow inputs.

    Attributes:
        module: Rego source code defining the policy.
        queries: Queries whose returned expressions describe violations.
    """

    @staticmethod
    def get_annotation_name() -> str:
        """Return the annotation key for Rego input policies."""
        return "eoap.ogc.org/inputs-rego-policy"

    module: str
    queries: list[str]

    @property
    def annotation(self) -> str:
        """Return the annotation key for Rego input policies."""
        return RegoPolicyHint.get_annotation_name()

    @model_serializer
    def ser_model(self) -> Mapping[str, Any]:
        """Serialize the policy module and queries as an annotation payload."""
        return {"queries": self.queries, "module": self.module}

    def validator(self) -> BaseValidator:
        """Create a Rego validator using this policy module and its queries."""
        from .rego_validator import RegoValidator

        return RegoValidator(queries=self.queries, module=self.module)


class Cql2Query(BaseModel):
    """Describe a CQL2 assertion and the violation reported when it is false.

    Attributes:
        id: Rule identifier used as the error pointer.
        cql2: CQL2 Text expression or CQL2 JSON expression mapping.
        message: Violation message to report when the predicate is false.
    """

    id: str
    cql2: str | Mapping[str, Any]
    message: str


class Cql2FilterHint(AssertionHint):
    """Configure CQL2 predicates for workflow inputs.

    Attributes:
        custom_functions: Optional trusted Python source executed to define
            functions available to the CQL2 evaluator.
        queries: Predicates that must evaluate to a truthy value.
    """

    @staticmethod
    def get_annotation_name() -> str:
        """Return the annotation key for CQL2 input filters."""
        return "eoap.ogc.org/inputs-cql2-filter"

    custom_functions: str | None = None
    queries: list[Cql2Query]

    @property
    def annotation(self) -> str:
        """Return the annotation key for CQL2 input filters."""
        return Cql2FilterHint.get_annotation_name()

    @model_serializer
    def ser_model(self) -> Mapping[str, Any]:
        """Serialize the queries as an annotation payload, omitting custom functions."""
        return {"queries": self.queries}

    def validator(self) -> BaseValidator:
        """Create a CQL2 validator with the configured queries and custom functions."""
        from .cql2_validator import Cql2Validator

        return Cql2Validator(custom_functions=self.custom_functions, queries=self.queries)


def _get_assertion_hint_by_name(
    parent_workflow: Any, hint: Mapping[str, Any]
) -> AssertionHint | None:
    """Resolve an eoap-prefixed hint class and instantiate its model.

    Args:
        parent_workflow: Parsed CWL process containing the hint.
        hint: Hint mapping with a class entry identifying the model.

    Returns:
        The instantiated hint, or None for an unrelated class or a failed model
        lookup or construction. Lookup and construction failures are logged.

    Raises:
        KeyError: If the hint has no class entry.
    """
    fqn_hint_kind = hint["class"]

    logger.debug(f"Analysing hint: {fqn_hint_kind}")

    if "eoap:" in fqn_hint_kind:
        hint_kind_name = fqn_hint_kind.split(":")[-1]

        logger.debug(f"Mapping {fqn_hint_kind} to {AssertionHint.__name__}:")

        try:
            hint_kind = globals()[hint_kind_name]
            if isinstance(hint_kind, type) and issubclass(hint_kind, AssertionHint):
                return hint_kind(parent_workflow=parent_workflow, **hint)
        except Exception as e:
            logger.error(
                f"An error occurred while mapping {fqn_hint_kind} to {AssertionHint.__name__}: {e}"
            )

    return None


def extract_assertion_hints(workflow: Any) -> list[AssertionHint]:
    """Collect recognized assertion hints from a parsed CWL process.

    Args:
        workflow: Parsed process exposing hints and CWL identification fields.

    Returns:
        Instantiated hints in declaration order. Non-dictionary hints, unrelated
        classes, and hints that fail model lookup or construction are skipped.

    Raises:
        KeyError: If a dictionary hint has no class entry.
    """
    assertion_hints = []

    if workflow.hints:
        for hint in workflow.hints:
            if isinstance(hint, dict):
                hint_instance = _get_assertion_hint_by_name(parent_workflow=workflow, hint=hint)

                if hint_instance:
                    assertion_hints.append(hint_instance)
    else:
        logger.debug(
            f"No hints defined in current #{workflow.id.split('#')[-1]} {workflow.class_} ({workflow.cwlVersion})"
        )

    return assertion_hints
