# app/core/cloud_tasks.py (only showing the changed parts)
from __future__ import annotations
import json
from typing import Mapping, Protocol
from app.core.config import settings


def _normalize_method(method: object | None) -> str:
    """Return an uppercased HTTP method string from str/enum/int/None."""
    if method is None:
        return "POST"
    if isinstance(method, str):
        return method.upper()
    # google enums usually have .name; IntEnum also has .name
    name = getattr(method, "name", None)
    if isinstance(name, str):
        return name.upper()
    # fallback if an int sneaks in (grpc enums)
    int_map = {
        1: "POST",
        2: "GET",
        3: "HEAD",
        4: "PUT",
        5: "DELETE",
        6: "PATCH",
        7: "OPTIONS",
    }
    if isinstance(method, int):
        return int_map.get(method, "POST")
    return "POST"


class TaskEnqueuer(Protocol):
    def enqueue_http_task(
        self,
        *,
        queue: str,
        url: str,
        method: str | None = None,
        headers: Mapping[str, str] | None = None,
        body: dict | None = None,
        oidc_audience: str | None = None,
    ) -> None: ...


USE_LOCAL = getattr(settings, "ENV", "").lower() == "dev"

if USE_LOCAL:
    import httpx

    class CloudTasksEnqueuer:
        def __init__(self):
            self.base = settings.BASE_URL.rstrip("/")

        def enqueue_http_task(
            self,
            *,
            queue: str,
            url: str,
            method: str | None = None,
            headers: Mapping[str, str] | None = None,
            body: dict | None = None,
            oidc_audience: str | None = None,
        ) -> None:
            target = url
            if not (target.startswith("http://") or target.startswith("https://")):
                if not target.startswith("/"):
                    target = "/" + target
                target = f"{self.base}{target}"

            req_headers = {"Content-Type": "application/json", **(headers or {})}
            m = _normalize_method(method)

            with httpx.Client(timeout=10.0) as client:
                resp = client.request(m, target, headers=req_headers, json=body)
                resp.raise_for_status()

else:
    from google.cloud import tasks_v2

    class CloudTasksEnqueuer:
        def __init__(self):
            self.client = tasks_v2.CloudTasksClient()

        def _queue_path(self, name: str) -> str:
            return self.client.queue_path(
                settings.GCP_PROJECT, settings.GCP_REGION, name
            )

        def enqueue_http_task(
            self,
            *,
            queue: str,
            url: str,
            method: str | None = None,
            headers: Mapping[str, str] | None = None,
            body: dict | None = None,
            oidc_audience: str | None = None,
        ) -> None:
            http_method = getattr(
                tasks_v2.HttpMethod, _normalize_method(method), tasks_v2.HttpMethod.POST
            )
            http_request: dict = {
                "http_method": http_method,
                "url": url,
                "headers": {"Content-Type": "application/json", **(headers or {})},
            }
            if body is not None:
                http_request["body"] = json.dumps(body).encode("utf-8")
            if getattr(settings, "TASKS_SERVICE_ACCOUNT_EMAIL", None) and oidc_audience:
                http_request["oidc_token"] = {
                    "service_account_email": settings.TASKS_SERVICE_ACCOUNT_EMAIL,
                    "audience": oidc_audience,
                }
            self.client.create_task(
                parent=self._queue_path(queue), task={"http_request": http_request}
            )
