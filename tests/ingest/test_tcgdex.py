from datetime import date

import httpx
import respx

from pokemon_tcg.ingest.tcgdex import BASE_URL, TcgdexIngester
from pokemon_tcg.records import LANGUAGE_JAPANESE

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


def _mock_tcgdex_api():
    respx.get(f"{BASE_URL}/sets").mock(return_value=httpx.Response(200, json=SETS_BRIEF))
    respx.get(f"{BASE_URL}/sets/PMCG1").mock(return_value=httpx.Response(200, json=SET_DETAIL))
    respx.get(f"{BASE_URL}/cards/PMCG1-001").mock(
        return_value=httpx.Response(200, json=CARD_DETAIL)
    )


@respx.mock
def test_japanese_cards_carry_language_end_to_end(tmp_path):
    _mock_tcgdex_api()
    ingester = TcgdexIngester(archive_root=tmp_path)
    raw = ingester.fetch()
    records = ingester.normalize(raw)

    assert records
    for record in records:
        assert record.language == LANGUAGE_JAPANESE


@respx.mock
def test_card_identity_fields_populated_from_api(tmp_path):
    _mock_tcgdex_api()
    ingester = TcgdexIngester(archive_root=tmp_path)
    raw = ingester.fetch()
    records = {r.card_key: r for r in ingester.normalize(raw)}

    record = records["pmcg1-1"]
    assert record.set_code == "PMCG1"
    assert record.number == "001"
    assert record.name == "フシギダネ"
    assert record.artist == "Mitsuhiro Arita"
    assert record.rarity == "Common"
    assert record.release_date == date(1996, 10, 20)


@respx.mock
def test_printing_finish_subset_and_tcgplayer_id_not_defaulted(tmp_path):
    _mock_tcgdex_api()
    ingester = TcgdexIngester(archive_root=tmp_path)
    raw = ingester.fetch()
    records = ingester.normalize(raw)

    for record in records:
        assert record.printing_variant is None
        assert record.finish is None
        assert record.subset is None
        assert record.tcgplayer_product_id is None


@respx.mock
def test_retries_on_transient_transport_error(tmp_path):
    route = respx.get(f"{BASE_URL}/sets")
    route.side_effect = [httpx.ConnectError("boom"), httpx.Response(200, json=SETS_BRIEF)]
    respx.get(f"{BASE_URL}/sets/PMCG1").mock(return_value=httpx.Response(200, json=SET_DETAIL))
    respx.get(f"{BASE_URL}/cards/PMCG1-001").mock(
        return_value=httpx.Response(200, json=CARD_DETAIL)
    )

    ingester = TcgdexIngester(archive_root=tmp_path)
    raw = ingester.fetch()

    assert route.call_count == 2
    assert raw


@respx.mock
def test_does_not_retry_on_permanent_client_error(tmp_path):
    route = respx.get(f"{BASE_URL}/sets")
    route.mock(return_value=httpx.Response(404, json={"error": "not found"}))

    ingester = TcgdexIngester(archive_root=tmp_path)
    try:
        ingester.fetch()
        raise AssertionError("expected fetch() to raise")
    except httpx.HTTPStatusError:
        pass

    assert route.call_count == 1


@respx.mock
def test_partial_fetch_is_archived_before_reraising_on_failure(tmp_path):
    respx.get(f"{BASE_URL}/sets").mock(return_value=httpx.Response(200, json=SETS_BRIEF))
    respx.get(f"{BASE_URL}/sets/PMCG1").mock(return_value=httpx.Response(500))

    ingester = TcgdexIngester(archive_root=tmp_path)
    try:
        ingester.fetch()
        raise AssertionError("expected fetch() to raise")
    except httpx.HTTPStatusError:
        pass

    archived = list((tmp_path / "tcgdex").glob("*.parquet"))
    assert len(archived) == 1


@respx.mock
def test_archive_writes_a_parquet_file_before_normalizing(tmp_path):
    _mock_tcgdex_api()
    ingester = TcgdexIngester(archive_root=tmp_path)
    raw = ingester.fetch()
    archive_path = ingester.archive(raw)

    assert archive_path.exists()
    assert archive_path.suffix == ".parquet"
