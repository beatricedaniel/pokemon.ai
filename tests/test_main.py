from pathlib import Path

import httpx
import respx

from pokemon_tcg.__main__ import main
from pokemon_tcg.ingest.tcgdex import BASE_URL
from pokemon_tcg.store.db import connect

FIXTURE_MIRROR = Path(__file__).parent / "fixtures" / "pokemon_tcg_data"

SETS_BRIEF = [{"id": "PMCG1", "name": "拡張パック"}]
SET_DETAIL = {
    "id": "PMCG1",
    "name": "拡張パック",
    "releaseDate": "1996-10-20",
    "cards": [{"id": "PMCG1-001", "localId": "001", "name": "フシギダネ"}],
}
CARD_DETAIL = {
    "id": "PMCG1-001",
    "localId": "001",
    "name": "フシギダネ",
    "illustrator": "Mitsuhiro Arita",
    "rarity": "Common",
    "set": {"id": "PMCG1", "name": "拡張パック"},
    "pricing": {"cardmarket": None, "tcgplayer": None},
}


def test_ingest_catalog_en_produces_nonzero_rows_in_duckdb(tmp_path):
    db_path = tmp_path / "pokemon.duckdb"

    main(
        [
            "ingest",
            "catalog-en",
            str(FIXTURE_MIRROR),
            "--db-path",
            str(db_path),
            "--archive-root",
            str(tmp_path / "raw"),
        ]
    )

    conn = connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM cards WHERE language = 'English'").fetchall()[0][0]
    assert count > 0


@respx.mock
def test_ingest_catalog_jp_produces_nonzero_rows_in_duckdb(tmp_path):
    respx.get(f"{BASE_URL}/sets").mock(return_value=httpx.Response(200, json=SETS_BRIEF))
    respx.get(f"{BASE_URL}/sets/PMCG1").mock(return_value=httpx.Response(200, json=SET_DETAIL))
    respx.get(f"{BASE_URL}/cards/PMCG1-001").mock(
        return_value=httpx.Response(200, json=CARD_DETAIL)
    )
    db_path = tmp_path / "pokemon.duckdb"

    main(
        ["ingest", "catalog-jp", "--db-path", str(db_path), "--archive-root", str(tmp_path / "raw")]
    )

    conn = connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM cards WHERE language = 'Japanese'").fetchall()[0][0]
    assert count > 0
