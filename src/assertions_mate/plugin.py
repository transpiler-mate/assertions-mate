# Copyright 2026 Terradue
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

"""Register the Assertions Mate plugin and run validation for CWL workflows."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — Pydantic resolves this type at runtime
from typing import TYPE_CHECKING, Annotated, Any

from cwl_utils.parser import Process, Workflow
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field
from ruamel.yaml import YAML
from transpiler_mate.api import (
    PluginFailureError,
    transpiler_plugin,
)

from . import extract_assertion_hints

if TYPE_CHECKING:
    from collections.abc import Mapping

    from transpiler_mate.api import TranspilerContext


class AssertionsMateOptions(BaseModel):
    """Options accepted by the Assertions Mate plugin.

    Attributes:
        inputs: Path to the YAML or JSON document containing workflow inputs.

    Unknown option fields are rejected.
    """

    model_config = ConfigDict(extra="forbid")

    inputs: Annotated[
        Path,
        Field(description="The Workflow inputs to check against the input Workflow"),
    ]


def _scan_workflow(wf: Process, inputs: Mapping[str, Any]):
    """Build a process's hint validators and log their validation results.

    Args:
        wf: Parsed CWL process whose assertion hints should be evaluated.
        inputs: Input mapping supplied to every configured validator.

    Raises:
        PluginFailureError: If a validator raises during input validation.

    Validator construction failures are logged and skipped. Returned violations
    are logged as warnings and do not raise an exception.
    """
    logger.info(
        "------------------------------------------------------------------------"
    )
    workflow_id = wf.id.split("#")[-1]
    logger.info(f"Validating #{workflow_id} {wf.class_} ({wf.cwlVersion}):")

    validators = []

    # prepare
    for hint_instance in extract_assertion_hints(wf):
        logger.info(f"Setting up validator for {type(hint_instance).__name__}...")

        try:
            validators.append(hint_instance.validator())
        except Exception as e:
            logger.error(
                f"An error occurred when setting up {type(hint_instance).__name__}: {e}"
            )

    if validators:
        logger.info("Setup is over, validating...")

        for validator in validators:
            logger.info(f"  - Executing {type(validator).__name__}...")

            try:
                problem_details = validator.validate_inputs(inputs)
            except Exception as exc:
                raise PluginFailureError(str(exc)) from exc
            if problem_details:
                logger.warning(
                    f"    {type(validator).__name__} detected violations below:"
                )

                for error_detail in problem_details.errors or []:
                    logger.warning(
                        f"    [{error_detail.pointer}] {error_detail.detail}"
                    )
            else:
                logger.info(
                    f"    {type(validator).__name__} execution terminated with no violations"
                )
    else:
        logger.info(f"No Validators configured in '#{workflow_id}.hints'")


@transpiler_plugin(
    name="assertions-mate",
    description="Scan, detect and perform all JSONSchemaHint/RegoPolicyHint/Cql2FilterHint for all Workflows declared in the CWL, against the inputs",
    options_model=AssertionsMateOptions,
)
def assertions_mate(context: TranspilerContext, options: AssertionsMateOptions) -> None:
    """Validate inputs against assertion hints on every workflow in the context.

    Args:
        context: Transpiler context providing the parsed CWL workflows.
        options: Plugin options identifying the input document to load.

    Raises:
        PluginFailureError: If a validator raises during input validation.
        OSError: If the input document cannot be opened or read.

    The same YAML-loaded input mapping is passed to each workflow. Document
    parsing errors propagate; returned validation violations are logged.
    """
    logger.info(f"Loading inputs from {options.inputs.absolute()}")

    with options.inputs.open() as input_stream:
        inputs_mapping: Mapping[str, Any] = YAML().load(input_stream)

    for workflow in context.get_processes_by_type(Workflow):
        _scan_workflow(workflow, inputs_mapping)
