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

"""Evaluate CQL2 Text and JSON assertions against workflow input mappings."""

from collections.abc import Mapping
from numbers import Integral, Real
from typing import Any

from eoap_problems_registry import (
    BusinessRuleViolation,
    ErrorDetail,
    ProblemDetails,
)
from loguru import logger
from pygeofilter.backends.native.evaluate import (  # type: ignore[import-untyped]
    NativeEvaluator,
)
from pygeofilter.parsers.cql2_json import (  # type: ignore[import-untyped]
    parse as parse_cql2_json,
)
from pygeofilter.parsers.cql2_text import (  # type: ignore[import-untyped]
    parse as parse_cql2_text,
)

from . import BaseValidator, Cql2Query


def _to_builtin(value: Any) -> Any:
    """Normalize YAML scalar wrappers to plain Python types."""
    if isinstance(value, Mapping):
        return {str(key): _to_builtin(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_builtin(item) for item in value]
    if isinstance(value, bool):
        value = bool(value)
    elif isinstance(value, str):
        value = str(value)
    elif isinstance(value, Integral):
        value = int(value)
    elif isinstance(value, Real):
        value = float(value)
    return value


class Cql2EvaluationError(RuntimeError):
    """A rule could not be evaluated, rather than evaluating to false."""


class Cql2Validator(BaseValidator):
    """Validate workflow inputs with CQL2 predicates and optional Python functions."""

    def __init__(self, queries: list[Cql2Query], custom_functions: str | None = None) -> None:
        """Initialize the native evaluator and retain the configured queries.

        Args:
            queries: Rules to evaluate against each input mapping.
            custom_functions: Trusted Python source executed immediately to populate
                the evaluator function map. Exceptions from this code propagate.
        """
        function_map: dict[str, Any] = {}

        if custom_functions:
            # SECURITY: CWL custom functions are trusted application code.
            # Loading untrusted workflows would permit arbitrary code execution.
            exec(custom_functions, function_map)  # nosec B102

        self.evaluator = NativeEvaluator(function_map=function_map, use_getattr=False)

        self.queries = queries

    def validate_inputs(self, data: Mapping[str, Any]) -> ProblemDetails | None:
        """Evaluate every configured CQL2 rule against the inputs.

        Args:
            data: Workflow input names mapped to their values.

        Returns:
            BusinessRuleViolation for malformed rules or false predicates, or None
            when all rules pass. Error pointers identify the corresponding rules.

        Raises:
            Cql2EvaluationError: If a parsed rule cannot be compiled or evaluated.
                Processing stops at that rule rather than returning a violation.
        """
        errors_list = []

        for query in self.queries:
            errors_list.extend(self._validate_query(query, data))

        if errors_list:
            return BusinessRuleViolation(errors=errors_list)

        return None

    def _validate_query(self, query: Cql2Query, data: Mapping[str, Any]) -> list[ErrorDetail]:
        """Parse and evaluate one rule, returning its validation errors.

        Raises:
            Cql2EvaluationError: If compilation or predicate execution fails.
        """
        errors_list = []
        ast = None

        if isinstance(query.cql2, str):
            try:
                ast = parse_cql2_text(query.cql2)
            except Exception as error:
                errors_list.append(
                    ErrorDetail(
                        pointer=query.id,
                        detail=f"Filter does not look like a valid CQL2 Text encoded sentece: {error}",
                    )
                )
        elif isinstance(query.cql2, dict):
            try:
                ast = parse_cql2_json(_to_builtin(query.cql2))
            except Exception as error:
                errors_list.append(
                    ErrorDetail(
                        pointer=query.id,
                        detail=f"Filter does not look like a valid CQL2 JSON encoded structure: {error}",
                    )
                )
        else:
            errors_list.append(
                ErrorDetail(
                    pointer=query.id,
                    detail=f"Filter is expressed in an unrecognizible format: {type(query.cql2)}",
                )
            )

        if ast and not self._evaluate_predicate(ast, data, query.id):
            errors_list.append(ErrorDetail(pointer=query.id, detail=query.message))

        return errors_list

    def _evaluate_predicate(self, ast: object, data: Mapping[str, Any], rule_id: str) -> bool:
        """Evaluate a parsed rule, wrapping evaluator failures with its identifier."""
        try:
            predicate = self.evaluator.evaluate(ast)
            return bool(predicate(data))
        except Exception as error:
            logger.opt(exception=True).debug("Failed to evaluate CQL2 rule '{}'", rule_id)
            raise Cql2EvaluationError(f"Could not evaluate rule '{rule_id}'") from error
