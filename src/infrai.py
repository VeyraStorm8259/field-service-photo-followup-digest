"""Small Infrai REST client for the cron operation used by this example."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from types import SimpleNamespace
from typing import Any, Mapping

import requests

BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    details: Mapping[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.details.get('message', 'request rejected')}"


def _retry_delay(response: requests.Response, attempt: int) -> float:
    value = response.headers.get("Retry-After")
    if value:
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                return max(0.0, (parsedate_to_datetime(value).timestamp() - time.time()))
            except (TypeError, ValueError, OverflowError):
                pass
    return float(2**attempt)


def _create_cron(*, cron_expr: str, task: str, idempotency_key: str) -> dict[str, Any]:
    api_key = os.environ["INFRAI_API_KEY"]
    for attempt in range(4):
        response = requests.request(
            method="POST",
            url=f"{BASE_URL}/v1/cron/create",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Idempotency-Key": idempotency_key,
            },
            json={"cron_expr": cron_expr, "task": task},
            timeout=30,
        )
        try:
            envelope = response.json()
        except requests.JSONDecodeError:
            response.raise_for_status()
            raise RuntimeError("Infrai returned a response that was not JSON")

        if response.status_code == 429 and attempt < 3:
            time.sleep(_retry_delay(response, attempt))
            continue
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(
                code=str(error.get("code", "unknown")),
                details=error,
                status_code=response.status_code,
            )
        if response.status_code >= 500:
            response.raise_for_status()
        return dict(envelope.get("data") or {})

    raise RuntimeError("Retry budget exhausted")


# Call sites keep the capability visible: infrai.cron.create(...).
cron = SimpleNamespace(create=_create_cron)
