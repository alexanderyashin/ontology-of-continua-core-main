from __future__ import annotations


def fetch_text(url: str) -> dict:
    return {"url": url, "state": "NOT_RUN", "reason": "Network fetch is reserved for postflight after explicit publication."}
