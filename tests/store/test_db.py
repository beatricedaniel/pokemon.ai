from datetime import UTC, datetime

from pokemon_tcg.records import LANGUAGE_ENGLISH, CardRecord
from pokemon_tcg.store.db import connect, upsert_cards


def _record(**overrides):
    defaults: dict = {
        "card_key": "base1-4",
        "set_code": "base1",
        "number": "4",
        "name": "Charizard",
        "language": LANGUAGE_ENGLISH,
        "rarity": "Rare Holo",
        "rarity_raw": "Rare Holo",
        "artist": "Mitsuhiro Arita",
        "release_date": None,
        "printing_variant": None,
        "finish": None,
        "subset": None,
        "tcgplayer_product_id": None,
    }
    defaults.update(overrides)
    return CardRecord(**defaults)


def test_upsert_inserts_new_card():
    conn = connect(":memory:")
    upsert_cards(conn, [_record()], computed_at=datetime(2026, 1, 1, tzinfo=UTC))

    rows = conn.execute("SELECT card_key, name FROM cards").fetchall()
    assert rows == [("base1-4", "Charizard")]


def test_reupsert_does_not_duplicate_row():
    conn = connect(":memory:")
    upsert_cards(conn, [_record()], computed_at=datetime(2026, 1, 1, tzinfo=UTC))
    upsert_cards(conn, [_record()], computed_at=datetime(2026, 1, 2, tzinfo=UTC))

    count = conn.execute("SELECT COUNT(*) FROM cards").fetchall()[0][0]
    assert count == 1


def test_reupsert_updates_identity_columns():
    conn = connect(":memory:")
    upsert_cards(conn, [_record(name="Charizard")], computed_at=datetime(2026, 1, 1, tzinfo=UTC))
    upsert_cards(
        conn,
        [_record(name="Charizard (corrected)")],
        computed_at=datetime(2026, 1, 2, tzinfo=UTC),
    )

    name = conn.execute("SELECT name FROM cards WHERE card_key = 'base1-4'").fetchall()[0][0]
    assert name == "Charizard (corrected)"


def test_reupsert_does_not_touch_segment_columns():
    conn = connect(":memory:")
    upsert_cards(conn, [_record()], computed_at=datetime(2026, 1, 1, tzinfo=UTC))
    conn.execute("UPDATE cards SET segment = 'vintage' WHERE card_key = 'base1-4'")

    upsert_cards(conn, [_record()], computed_at=datetime(2026, 1, 2, tzinfo=UTC))

    segment = conn.execute("SELECT segment FROM cards WHERE card_key = 'base1-4'").fetchall()[0][0]
    assert segment == "vintage"
