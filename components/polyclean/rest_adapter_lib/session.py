from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def build_session(
    retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> requests.Session:
    """Return a requests.Session pre-configured with retry logic.

    Args:
        retries: Total number of retry attempts.
        backoff_factor: Sleep between retries follows: {backoff_factor} * (2 ** (attempt - 1)).
        status_forcelist: HTTP status codes that trigger a retry.

    Example::

        session = build_session(retries=3)
        response = session.get("https://api.example.com/data", timeout=15)

    """
    retry_policy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods={"GET", "POST"},
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_policy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session
