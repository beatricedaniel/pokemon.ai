from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

import httpx
import polars as pl
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from pokemon_tcg.records import CardRecord


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and (
        exc.response.status_code == 429 or exc.response.status_code >= 500
    )


# Shared retry policy (AD-5): 3 attempts, exponential backoff, only on transport
# errors and 429/5xx — a permanent 4xx still raises immediately, retry can't fix it.
retry_on_transient_error = retry(
    retry=retry_if_exception(_is_transient),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)


class Ingester(Protocol):
    def fetch(self) -> Any: ...
    def archive(self, raw: Any) -> Path: ...
    def normalize(self, raw: Any) -> list[CardRecord]: ...


def archive_raw_json(
    entries: list[tuple[str, bytes]], *, source: str, archive_root: Path, fetched_at: datetime
) -> Path:
    """Archive raw fetch responses to bronze Parquet before normalization (AD-1)."""
    archive_dir = archive_root / source
    archive_dir.mkdir(parents=True, exist_ok=True)
    path = archive_dir / f"{fetched_at.strftime('%Y%m%dT%H%M%S%f')}.parquet"
    pl.DataFrame(
        {
            "fetched_at": [fetched_at] * len(entries),
            "name": [name for name, _ in entries],
            "raw_json": [payload.decode("utf-8") for _, payload in entries],
        }
    ).write_parquet(path)
    return path
