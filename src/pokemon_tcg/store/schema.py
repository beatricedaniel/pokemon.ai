# All DDL lives here, one place, no migration framework (single user, single file).
# Segment columns are written only by features/segment.py once that story lands;
# declared now so a later story never needs a schema migration (AD-2, AD-10).
CARDS_DDL = """
CREATE TABLE IF NOT EXISTS cards (
    card_key TEXT PRIMARY KEY,
    set_code TEXT NOT NULL,
    number TEXT NOT NULL,
    name TEXT NOT NULL,
    language TEXT NOT NULL,
    rarity TEXT NOT NULL,
    rarity_raw TEXT,
    artist TEXT,
    release_date DATE,
    printing_variant TEXT,
    finish TEXT,
    subset TEXT,
    tcgplayer_product_id TEXT,
    segment TEXT,
    segment_reason TEXT,
    segment_version TEXT,
    computed_at TIMESTAMP NOT NULL
)
"""
