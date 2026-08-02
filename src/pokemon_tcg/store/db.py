from datetime import datetime
from pathlib import Path

import duckdb

from pokemon_tcg.records import CardRecord
from pokemon_tcg.store.schema import CARDS_DDL

# Identity columns only (AD-2): cards.segment/segment_reason/segment_version are
# owned and written exclusively by features/segment.py, never by an ingester.
_UPSERT_CARDS_SQL = """
INSERT INTO cards (
    card_key, set_code, number, name, language, rarity, rarity_raw,
    artist, release_date, printing_variant, finish, subset,
    tcgplayer_product_id, computed_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (card_key) DO UPDATE SET
    set_code = excluded.set_code,
    number = excluded.number,
    name = excluded.name,
    language = excluded.language,
    rarity = excluded.rarity,
    rarity_raw = excluded.rarity_raw,
    artist = excluded.artist,
    release_date = excluded.release_date,
    printing_variant = excluded.printing_variant,
    finish = excluded.finish,
    subset = excluded.subset,
    tcgplayer_product_id = excluded.tcgplayer_product_id,
    computed_at = excluded.computed_at
"""


def connect(db_path: Path | str) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(db_path))
    conn.execute(CARDS_DDL)
    return conn


def upsert_cards(
    conn: duckdb.DuckDBPyConnection, records: list[CardRecord], computed_at: datetime
) -> None:
    if not records:
        return
    rows = [
        (
            r.card_key,
            r.set_code,
            r.number,
            r.name,
            r.language,
            r.rarity,
            r.rarity_raw,
            r.artist,
            r.release_date,
            r.printing_variant,
            r.finish,
            r.subset,
            r.tcgplayer_product_id,
            computed_at,
        )
        for r in records
    ]
    conn.executemany(_UPSERT_CARDS_SQL, rows)
