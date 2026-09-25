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

"""Validate workflow inputs with JSON Schema Draft 2020-12 and remote references."""

import json
from collections.abc import Callable, Mapping
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from eoap_problems_registry import (
    ErrorDetail,
    InvalidBodyPropertyFormat,
    ProblemDetails,
)
from jsonschema import Draft202012Validator
from referencing import Registry as ReferencingRegistry
from referencing import Resource
from referencing.exceptions import NoSuchResource
from referencing.jsonschema import DRAFT202012
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from . import BaseValidator

_REMOTE_SCHEMA_TIMEOUT_SECONDS = 10


class JSONSchemaRegistry:
    """Retrieve JSON or YAML schema documents through a Requests session."""

    def __init__(
        self,
        timeout: int = _REMOTE_SCHEMA_TIMEOUT_SECONDS,
    ):
        """Create a session for schema retrieval.

        Args:
            timeout: Timeout in seconds passed to each schema HTTP request.
        """
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "assertions-mate"})
        self.timeout = timeout

    @staticmethod
    def _schema_format_from_content_type(content_type: str | None) -> str | None:
        """Infer json or yaml from a media type, or return None if unrecognized."""
        if not content_type:
            return None

        media_type = content_type.split(";", 1)[0].strip().lower()

        if media_type == "application/json" or media_type.endswith("+json"):
            return "json"

        if media_type in {
            "application/yaml",
            "application/x-yaml",
            "text/yaml",
            "text/x-yaml",
        } or media_type.endswith("+yaml"):
            return "yaml"

        return None

    @staticmethod
    def _schema_format_from_uri(uri: str) -> str | None:
        """Infer json or yaml from a URI path suffix, or return None."""
        path = urlparse(uri).path.lower()

        if path.endswith(".json"):
            return "json"

        if path.endswith((".yaml", ".yml")):
            return "yaml"

        return None

    def _parse_schema(
        self,
        payload: bytes,
        uri: str,
        content_type: str | None = None,
    ) -> Any:
        """Decode a UTF-8 schema document as JSON or YAML.

        Args:
            payload: Schema document bytes.
            uri: Document URI, used for format detection and error reporting.
            content_type: Optional HTTP media type, preferred over the URI suffix.

        Returns:
            The parsed document. If the preferred parser fails, try the other format.

        Raises:
            UnicodeDecodeError: If the payload is not valid UTF-8.
            ValueError: If both JSON and YAML parsing fail.
        """
        text = payload.decode("utf-8")
        preferred_format = (
            self._schema_format_from_content_type(content_type)
            or self._schema_format_from_uri(uri)
            or "json"
        )
        parsers: tuple[Callable[[str], object], ...] = (json.loads, YAML().load)
        if preferred_format == "yaml":
            parsers = parsers[::-1]
        preferred_parser, fallback_parser = parsers
        try:
            return preferred_parser(text)
        except (ValueError, YAMLError):
            pass
        try:
            return fallback_parser(text)
        except (ValueError, YAMLError) as error:
            raise ValueError(f"Unable to parse JSON Schema from {uri}") from error

    @staticmethod
    def _schema_request_uri(uri: str) -> str:
        """Preserve a URI scheme or convert an existing path to a file URI.

        Raises:
            NoSuchResource: If a schemeless path does not exist.

        Converting a path does not install a Requests adapter for file URIs.
        """
        parsed_uri = urlparse(uri)
        if parsed_uri.scheme:
            return uri

        path = Path(uri)
        if not path.exists():
            raise NoSuchResource(uri)

        return path.absolute().as_uri()

    def load_schema(self, uri: str) -> Any:
        """Fetch a schema document and parse it as JSON or YAML.

        Args:
            uri: Schema location supported by the configured Requests session.
                The default session supports HTTP and HTTPS, not local files.

        Returns:
            The parsed schema document.

        Raises:
            NoSuchResource: If a path is missing, the URI scheme has no adapter,
                or the server returns HTTP 404.
            requests.exceptions.RequestException: If the request otherwise fails.
            UnicodeDecodeError: If the response is not valid UTF-8.
            ValueError: If the response cannot be parsed as JSON or YAML.
        """
        try:
            response = self.session.get(
                self._schema_request_uri(uri),
                timeout=self.timeout,
            )
        except requests.exceptions.InvalidSchema as error:
            raise NoSuchResource(uri) from error

        if response.status_code == HTTPStatus.NOT_FOUND.value:
            raise NoSuchResource(uri)

        response.raise_for_status()

        return self._parse_schema(
            payload=response.content,
            uri=uri,
            content_type=response.headers.get("Content-Type"),
        )

    def retrieve(self, uri: str) -> Resource[Any]:
        """Load a URI as a Draft 2020-12 resource for reference resolution.

        Args:
            uri: Schema location to fetch through load_schema.

        Returns:
            A schema resource wrapping the parsed document.

        Retrieval and parsing errors from load_schema propagate to the caller.
        """
        return DRAFT202012.create_resource(self.load_schema(uri))

    def as_referencing_registry(self) -> ReferencingRegistry[Any]:
        # mypy does not understand the attrs field alias used by referencing.
        """Create a referencing registry backed by this instance's retrieval callback."""
        return ReferencingRegistry(retrieve=self.retrieve)  # type: ignore[call-arg]


class JSONSchemaValidator(BaseValidator):
    """Validate input mappings against a JSON Schema Draft 2020-12 schema."""

    def __init__(
        self,
        schema: Mapping[str, Any],
    ):
        """Configure schema validation and retrieval of referenced schemas.

        Args:
            schema: JSON Schema document describing accepted workflow inputs.
        """
        self.validator = Draft202012Validator(
            schema,
            registry=JSONSchemaRegistry().as_referencing_registry(),
        )

    def validate_inputs(self, data: Mapping[str, Any]) -> ProblemDetails | None:
        """Collect schema violations for a workflow input mapping.

        Args:
            data: Workflow input names mapped to their values.

        Returns:
            InvalidBodyPropertyFormat containing schema violations, or None when
            the inputs conform to the schema.

        Schema evaluation and reference resolution errors propagate to the caller.
        """
        errors_list = []

        for error in self.validator.iter_errors(data):
            print(error.__dict__)

            errors_list.append(
                ErrorDetail(
                    detail=error.message,
                    pointer=f"#/{'/'.join(error.path)}"
                    if error.path and isinstance(error.path, str)
                    else None,
                    code=".".join(error.schema_path),
                )
            )

        if errors_list:
            return InvalidBodyPropertyFormat(errors=errors_list)

        return None
