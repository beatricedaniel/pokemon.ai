import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx

from pokemon_tcg.ids import card_key
from pokemon_tcg.ingest.base import archive_raw_json, retry_on_transient_error
from pokemon_tcg.rarity import normalize_rarity
from pokemon_tcg.records import LANGUAGE_JAPANESE, CardRecord

SOURCE = "tcgdex"
BASE_URL = "https://api.tcgdex.net/v2/ja"


class TcgdexIngester:
    """Live-api ingester for TCGdex's Japanese catalog (FR-1, FR-2).

    pokemon-tcg-data has no Japanese sets; TCGdex is the only offline-cloneable
    alternative found, and its data is TypeScript source rather than flat JSON,
    so this calls its free, no-auth JSON API instead of a static clone.
    """

    def __init__(self, archive_root: Path = Path("data/raw")) -> None:
        self.archive_root = archive_root

    @retry_on_transient_error
    def _get(self, path: str) -> Any:
        response = httpx.get(f"{BASE_URL}{path}", timeout=10.0)
        response.raise_for_status()
        return response.json()

    def fetch(self) -> list[tuple[str, bytes]]:
        entries: list[tuple[str, bytes]] = []
        try:
            sets_brief = self._get("/sets")
            entries.append(("sets", json.dumps(sets_brief).encode()))
            for set_brief in sets_brief:
                set_id = set_brief["id"]
                set_detail = self._get(f"/sets/{set_id}")
                entries.append((f"sets/{set_id}", json.dumps(set_detail).encode()))
                for card_brief in set_detail.get("cards", []):
                    card_id = card_brief["id"]
                    card_detail = self._get(f"/cards/{card_id}")
                    entries.append((f"cards/{card_id}", json.dumps(card_detail).encode()))
        except httpx.HTTPError:
            # A full crawl is thousands of requests; archive whatever was
            # already fetched so a mid-run failure doesn't discard it all.
            if entries:
                self.archive(entries)
            raise
        return entries

    def archive(self, raw: list[tuple[str, bytes]]) -> Path:
        return archive_raw_json(
            raw, source=SOURCE, archive_root=self.archive_root, fetched_at=datetime.now(UTC)
        )

    def normalize(self, raw: list[tuple[str, bytes]]) -> list[CardRecord]:
        entries = dict(raw)
        release_dates = {
            name.removeprefix("sets/"): _parse_release_date(json.loads(payload).get("releaseDate"))
            for name, payload in entries.items()
            if name.startswith("sets/")
        }
        records = []
        for name, payload in entries.items():
            if not name.startswith("cards/"):
                continue
            card = json.loads(payload)
            set_id = card["set"]["id"]
            number = card["localId"]
            rarity_raw = card.get("rarity")
            records.append(
                CardRecord(
                    card_key=card_key(set_id, number),
                    set_code=set_id,
                    number=number,
                    name=card["name"],
                    language=LANGUAGE_JAPANESE,
                    rarity=normalize_rarity(rarity_raw),
                    rarity_raw=rarity_raw,
                    artist=card.get("illustrator"),
                    release_date=release_dates.get(set_id),
                    # variants (holo/reverse/normal/firstEdition) is a multi-flag
                    # bag, not a single value per card; collapsing it to one
                    # printing_variant/finish would be guessing, so left missing.
                    printing_variant=None,
                    finish=None,
                    subset=None,
                    # TCGdex's pricing.tcgplayer has never been observed populated
                    # for a Japanese card; not defaulted to a guessed field shape.
                    tcgplayer_product_id=None,
                )
            )
        return records


def _parse_release_date(raw: str | None) -> date | None:
    if raw is None:
        return None
    return date.fromisoformat(raw)
