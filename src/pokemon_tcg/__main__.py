import argparse
from datetime import UTC, datetime
from pathlib import Path

from pokemon_tcg.ingest.base import Ingester
from pokemon_tcg.ingest.catalog_mirror import CatalogMirrorIngester
from pokemon_tcg.ingest.tcgdex import TcgdexIngester
from pokemon_tcg.store.db import connect, upsert_cards

DEFAULT_DB_PATH = Path("data/pokemon.duckdb")
DEFAULT_ARCHIVE_ROOT = Path("data/raw")


def _run_ingest(ingester: Ingester, db_path: Path, label: str) -> None:
    raw = ingester.fetch()
    ingester.archive(raw)
    records = ingester.normalize(raw)
    conn = connect(db_path)
    upsert_cards(conn, records, computed_at=datetime.now(UTC))
    print(f"Ingested {len(records)} {label} cards into {db_path}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="pokemon_tcg")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest")
    ingest_subparsers = ingest_parser.add_subparsers(dest="ingest_target", required=True)

    catalog_en_parser = ingest_subparsers.add_parser("catalog-en")
    catalog_en_parser.add_argument("mirror_path", type=Path)
    catalog_en_parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    catalog_en_parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)

    catalog_jp_parser = ingest_subparsers.add_parser("catalog-jp")
    catalog_jp_parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    catalog_jp_parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)

    args = parser.parse_args(argv)

    if args.ingest_target == "catalog-en":
        ingester = CatalogMirrorIngester(
            mirror_path=args.mirror_path, archive_root=args.archive_root
        )
        _run_ingest(ingester, args.db_path, "English")
    elif args.ingest_target == "catalog-jp":
        ingester = TcgdexIngester(archive_root=args.archive_root)
        _run_ingest(ingester, args.db_path, "Japanese")


if __name__ == "__main__":
    main()
