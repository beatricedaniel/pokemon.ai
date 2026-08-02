from dataclasses import dataclass
from datetime import date

LANGUAGE_ENGLISH = "English"
LANGUAGE_JAPANESE = "Japanese"


@dataclass(frozen=True, slots=True)
class CardRecord:
    card_key: str
    set_code: str
    number: str
    name: str
    language: str
    rarity: str
    rarity_raw: str | None
    artist: str | None
    release_date: date | None
    printing_variant: str | None
    finish: str | None
    subset: str | None
    tcgplayer_product_id: str | None
