"""Small authenticated client for the BreakCheck HTTP API."""

from __future__ import annotations

import os
from typing import Any

import requests


DEFAULT_API_URL = os.getenv("BREAKCHECK_API_URL", "http://127.0.0.1:8000").rstrip("/")


class APIError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BreakCheckAPI:
    def __init__(self, base_url: str = DEFAULT_API_URL, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = requests.Session()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = dict(kwargs.pop("headers", {}))
        if self.token:
            headers["X-Session-Token"] = self.token
        try:
            response = self.session.request(
                method, f"{self.base_url}{path}", headers=headers, timeout=25, **kwargs
            )
        except requests.RequestException as error:
            raise APIError(
                f"Cannot reach the API at {self.base_url}. Start the API service and try again."
            ) from error

        if not response.ok:
            try:
                detail = response.json().get("detail", response.text)
            except (ValueError, AttributeError):
                detail = response.text
            raise APIError(str(detail), response.status_code)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def sign_in(self, username: str, password: str) -> dict[str, Any]:
        result = self._request(
            "POST", "/auth/sign-in", json={"username": username, "password": password}
        )
        self.token = result["session_token"]
        return result

    def sign_out(self) -> None:
        if self.token:
            self._request("POST", "/auth/signout")

    def get(self, path: str, **kwargs: Any) -> Any:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, body: dict[str, Any]) -> Any:
        return self._request("POST", path, json=body)
