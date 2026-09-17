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

"""Evaluate Rego policies that return workflow input violation messages."""

from collections.abc import Mapping
from typing import Any

from eoap_problems_registry import BusinessRuleViolation, ErrorDetail, ProblemDetails
from regopy import Interpreter  # type: ignore[import-untyped]
from regopy.interpreter import Input  # type: ignore[import-untyped]

from . import BaseValidator


class RegoValidator(BaseValidator):
    """Run Rego queries and collect their returned expressions as violations."""

    def __init__(self, module: str, queries: list[str]):
        """Load a policy module into a Rego interpreter.

        Args:
            module: Rego source registered under the interpreter module name workflow.
            queries: Queries to run after setting the workflow inputs.

        Policy loading errors propagate from the interpreter.
        """
        self.rego = Interpreter()
        self.rego.add_module("workflow", module)
        self.queries = queries

    def validate_inputs(self, data: Mapping[str, Any]) -> ProblemDetails | None:
        """Set the Rego input document and collect query result expressions.

        Args:
            data: Workflow input mapping exposed to policies as input.

        Returns:
            BusinessRuleViolation containing one error per returned expression,
            with the query as its pointer, or None when no expressions are returned.
            Expressions are converted to strings without testing their truthiness.

        Interpreter errors propagate to the caller.
        """
        errors_list = []

        self.rego.set_input(Input(data))

        for query in self.queries:
            for result in self.rego.query(query):
                # result.expressions is a list of Expression objects
                exprs = result.expressions
                if not exprs:  # safety check
                    continue

                for expr in exprs:
                    errors_list.append(ErrorDetail(pointer=query, detail=str(expr)))

        if errors_list:
            return BusinessRuleViolation(errors=errors_list)

        return None
