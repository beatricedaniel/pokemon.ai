from datetime import date
from pathlib import Path

from pokemon_tcg.ingest.catalog_mirror import CatalogMirrorIngester
from pokemon_tcg.rarity import UNMAPPED_RARITY
from pokemon_tcg.records import LANGUAGE_ENGLISH

FIXTURE_MIRROR = Path(__file__).parent.parent / "fixtures" / "pokemon_tcg_data"


def _ingest(tmp_path):
    ingester = CatalogMirrorIngester(mirror_path=FIXTURE_MIRROR, archive_root=tmp_path)
    raw = ingester.fetch()
    ingester.archive(raw)
    return ingester.normalize(raw)


def test_every_card_has_required_identity_fields(tmp_path):
    records = _ingest(tmp_path)
    assert records
    for record in records:
        assert record.card_key
        assert record.set_code
        assert record.number
        assert record.name
        assert record.language == LANGUAGE_ENGLISH


def test_card_keys_stable_across_reingestion(tmp_path):
    first = {r.card_key for r in _ingest(tmp_path)}
    second = {r.card_key for r in _ingest(tmp_path)}
    assert first == second


def test_distinct_printings_get_distinct_card_keys(tmp_path):
    records = _ingest(tmp_path)
    keys = [r.card_key for r in records]
    assert len(keys) == len(set(keys))


def test_known_rarity_is_mapped(tmp_path):
    records = {r.card_key: r for r in _ingest(tmp_path)}
    charizard = records["base1-4"]
    assert charizard.rarity == "Rare Holo"
    assert charizard.rarity_raw == "Rare Holo"


def test_unknown_rarity_is_flagged_unmapped_not_leaked(tmp_path):
    records = {r.card_key: r for r in _ingest(tmp_path)}
    alakazam = records["base1-1"]
    assert alakazam.rarity == UNMAPPED_RARITY
    assert alakazam.rarity_raw == "A Rarity Nobody Has Mapped Yet"


def test_missing_artist_recorded_as_missing_not_guessed(tmp_path):
    records = {r.card_key: r for r in _ingest(tmp_path)}
    assert records["base1-1"].artist is None


def test_release_date_parsed_from_set_metadata(tmp_path):
    records = {r.card_key: r for r in _ingest(tmp_path)}
    assert records["base1-4"].release_date == date(1999, 1, 9)


def test_set_missing_release_date_recorded_as_missing(tmp_path):
    records = {r.card_key: r for r in _ingest(tmp_path)}
    assert records["swshp-swsh001"].release_date is None


def test_printing_finish_subset_and_tcgplayer_id_not_provided_by_mirror(tmp_path):
    records = _ingest(tmp_path)
    for record in records:
        assert record.printing_variant is None
        assert record.finish is None
        assert record.subset is None
        assert record.tcgplayer_product_id is None


def test_archive_writes_a_parquet_file_before_normalizing(tmp_path):
    ingester = CatalogMirrorIngester(mirror_path=FIXTURE_MIRROR, archive_root=tmp_path)
    raw = ingester.fetch()
    archive_path = ingester.archive(raw)
    assert archive_path.exists()
    assert archive_path.suffix == ".parquet"
