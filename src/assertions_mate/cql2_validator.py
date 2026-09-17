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
        return {str(k): _to_builtin(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_builtin(v) for v in value]
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, str):
        return str(value)
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real):
        return float(value)
    return value


class Cql2EvaluationError(RuntimeError):
    """A rule could not be evaluated, rather than evaluating to false."""


class Cql2Validator(BaseValidator):
    def __init__(self, queries: list[Cql2Query], custom_functions: str | None = None):
        function_map: dict[str, Any] = {}

        if custom_functions:
            # SECURITY: CWL custom functions are trusted application code.
            # Loading untrusted workflows would permit arbitrary code execution.
            exec(custom_functions, function_map)  # nosec B102

        self.evaluator = NativeEvaluator(function_map=function_map, use_getattr=False)

        self.queries = queries

    def validate_inputs(self, data: Mapping[str, Any]) -> ProblemDetails | None:
        errors_list = []

        for filter in self.queries:
            ast = None

            if isinstance(filter.cql2, str):
                try:
                    ast = parse_cql2_text(filter.cql2)
                except Exception as e:
                    errors_list.append(
                        ErrorDetail(
                            pointer=filter.id,
                            detail=f"Filter does not look like a valid CQL2 Text encoded sentece: {e}",
                        )
                    )
            elif isinstance(filter.cql2, dict):
                try:
                    ast = parse_cql2_json(_to_builtin(filter.cql2))
                except Exception as e:
                    errors_list.append(
                        ErrorDetail(
                            pointer=filter.id,
                            detail=f"Filter does not look like a valid CQL2 JSON encoded structure: {e}",
                        )
                    )
            else:
                errors_list.append(
                    ErrorDetail(
                        pointer=filter.id,
                        detail=f"Filter is expressed in an unrecognizible format: {type(filter.cql2)}",
                    )
                )

            if ast:
                try:
                    predicate = self.evaluator.evaluate(ast)

                    if not predicate(data):
                        errors_list.append(
                            ErrorDetail(pointer=filter.id, detail=filter.message)
                        )
                except Exception as e:
                    logger.opt(exception=True).debug(
                        "Failed to evaluate CQL2 rule '{}'", filter.id
                    )
                    raise Cql2EvaluationError(
                        f"Could not evaluate rule '{filter.id}'"
                    ) from e

        if errors_list:
            return BusinessRuleViolation(errors=errors_list)

        return None
