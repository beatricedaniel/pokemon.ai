import json
from datetime import UTC, date, datetime
from pathlib import Path

from pokemon_tcg.ids import card_key
from pokemon_tcg.ingest.base import archive_raw_json
from pokemon_tcg.rarity import normalize_rarity
from pokemon_tcg.records import LANGUAGE_ENGLISH, CardRecord

SOURCE = "pokemon-tcg-data"


class CatalogMirrorIngester:
    """Static-mirror ingester for the offline PokemonTCG/pokemon-tcg-data clone (FR-1, FR-2)."""

    def __init__(self, mirror_path: Path, archive_root: Path = Path("data/raw")) -> None:
        self.mirror_path = mirror_path
        self.archive_root = archive_root

    def fetch(self) -> list[tuple[str, bytes]]:
        sets_path = self.mirror_path / "sets" / "en.json"
        entries = [(sets_path.relative_to(self.mirror_path).as_posix(), sets_path.read_bytes())]
        cards_dir = self.mirror_path / "cards" / "en"
        for card_file in sorted(cards_dir.glob("*.json")):
            name = card_file.relative_to(self.mirror_path).as_posix()
            entries.append((name, card_file.read_bytes()))
        return entries

    def archive(self, raw: list[tuple[str, bytes]]) -> Path:
        return archive_raw_json(
            raw, source=SOURCE, archive_root=self.archive_root, fetched_at=datetime.now(UTC)
        )

    def normalize(self, raw: list[tuple[str, bytes]]) -> list[CardRecord]:
        entries = dict(raw)
        sets_by_id = {s["id"]: s for s in json.loads(entries["sets/en.json"])}
        records = []
        for name, payload in entries.items():
            if name == "sets/en.json":
                continue
            set_id = Path(name).stem
            release_date = _parse_release_date(sets_by_id.get(set_id, {}).get("releaseDate"))
            for card in json.loads(payload):
                number = card["number"]
                rarity_raw = card.get("rarity")
                records.append(
                    CardRecord(
                        card_key=card_key(set_id, number),
                        set_code=set_id,
                        number=number,
                        name=card["name"],
                        language=LANGUAGE_ENGLISH,
                        rarity=normalize_rarity(rarity_raw),
                        rarity_raw=rarity_raw,
                        artist=card.get("artist"),
                        release_date=release_date,
                        # pokemon-tcg-data's card JSON has no printing/edition,
                        # finish, subset, or TCGplayer product id fields at all;
                        # recorded as missing rather than defaulted or guessed.
                        printing_variant=None,
                        finish=None,
                        subset=None,
                        tcgplayer_product_id=None,
                    )
                )
        return records


def _parse_release_date(raw: str | None) -> date | None:
    if raw is None:
        return None
    return datetime.strptime(raw, "%Y/%m/%d").replace(tzinfo=UTC).date()
