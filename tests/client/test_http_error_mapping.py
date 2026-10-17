# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: AGPL-3.0

"""Focused tests for SDK HTTP error-code mapping."""

import pytest

from openviking_cli.client.http import AsyncHTTPClient
from openviking_cli.exceptions import (
    AbortedError,
    ConflictError,
    DeadlineExceededError,
    NotInitializedError,
    OpenVikingError,
    ResourceExhaustedError,
    SessionExpiredError,
    UnavailableError,
    UnimplementedError,
)


@pytest.mark.parametrize(
    ("code", "exc_type"),
    (
        ("CONFLICT", ConflictError),
        ("ABORTED", AbortedError),
        ("RESOURCE_EXHAUSTED", ResourceExhaustedError),
        ("UNIMPLEMENTED", UnimplementedError),
    ),
)
def test_client_maps_standard_error_codes(code, exc_type):
    client = AsyncHTTPClient(url="http://127.0.0.1:1933")

    with pytest.raises(exc_type) as exc_info:
        client._raise_exception({"code": code, "message": "mapped"})

    assert exc_info.value.code == code


def test_client_maps_resource_exhausted_error_code():
    client = AsyncHTTPClient(url="http://127.0.0.1:1933")

    with pytest.raises(ResourceExhaustedError) as exc_info:
        client._raise_exception(
            {
                "code": "RESOURCE_EXHAUSTED",
                "message": "Upstream model quota or rate limit exceeded",
                "details": {"upstream_status_code": 429},
            }
        )

    assert exc_info.value.code == "RESOURCE_EXHAUSTED"
    assert exc_info.value.details == {"upstream_status_code": 429}


def test_client_preserves_unknown_error_code():
    client = AsyncHTTPClient(url="http://127.0.0.1:1933")

    with pytest.raises(OpenVikingError) as exc_info:
        client._raise_exception(
            {
                "code": "PROVIDER_SPECIFIC",
                "message": "provider-specific failure",
                "details": {"x": 1},
            }
        )

    assert exc_info.value.code == "PROVIDER_SPECIFIC"
    assert exc_info.value.details == {"x": 1}


@pytest.mark.parametrize(
    ("code", "exc_type", "message", "details"),
    (
        (
            "DEADLINE_EXCEEDED",
            DeadlineExceededError,
            "Queue processing timed out",
            {"operation": "queue processing", "timeout": None},
        ),
        (
            "DEADLINE_EXCEEDED",
            DeadlineExceededError,
            "Upstream model request timed out: ReadTimeout",
            {"upstream_message": "ReadTimeout"},
        ),
        (
            "NOT_INITIALIZED",
            NotInitializedError,
            "Vikingfs not initialized. Call initialize() first.",
            {"component": "VikingFS"},
        ),
        (
            "SESSION_EXPIRED",
            SessionExpiredError,
            "Session expired: s1",
            {"session_id": "s1"},
        ),
        (
            "UNAVAILABLE",
            UnavailableError,
            "Storage backend unavailable: lock contention",
            {"service": "storage backend", "reason": "lock contention"},
        ),
        (
            "UNAVAILABLE",
            UnavailableError,
            "Upstream model service unavailable (HTTP 503): overloaded",
            {"upstream_message": "overloaded", "upstream_status_code": 503},
        ),
    ),
)
def test_client_keeps_server_formatted_error_message(code, exc_type, message, details):
    client = AsyncHTTPClient(url="http://127.0.0.1:1933")

    with pytest.raises(exc_type) as exc_info:
        client._raise_exception({"code": code, "message": message, "details": details})

    assert str(exc_info.value) == message
    assert exc_info.value.message == message
    assert exc_info.value.code == code
    assert exc_info.value.details == details
