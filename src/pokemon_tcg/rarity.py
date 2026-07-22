UNMAPPED_RARITY = "unmapped"

# Built from rarity strings actually observed in pokemon-tcg-data (English,
# base1 through sv1 plus promos) and TCGdex (Japanese). Anything not listed
# here is flagged unmapped rather than guessed.
_RARITY_VOCABULARY: dict[str, str] = {
    "Common": "Common",
    "Uncommon": "Uncommon",
    "Rare": "Rare",
    "Rare Holo": "Rare Holo",
    "Holo Rare": "Rare Holo",
    "Rare Holo EX": "Ultra Rare",
    "Rare Holo GX": "Ultra Rare",
    "Rare Holo V": "Ultra Rare",
    "Rare Holo VMAX": "Ultra Rare",
    "Rare Ultra": "Ultra Rare",
    "Ultra Rare": "Ultra Rare",
    "Double Rare": "Double Rare",
    "Rare Secret": "Secret Rare",
    "Rare Rainbow": "Secret Rare",
    "Hyper Rare": "Secret Rare",
    "Illustration Rare": "Illustration Rare",
    "Special Illustration Rare": "Illustration Rare",
    "Promo": "Promo",
}


def normalize_rarity(raw: str | None) -> str:
    """Map a source rarity string to the controlled vocabulary, or UNMAPPED_RARITY."""
    if raw is None:
        return UNMAPPED_RARITY
    return _RARITY_VOCABULARY.get(raw, UNMAPPED_RARITY)
