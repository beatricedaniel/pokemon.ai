def card_key(set_code: str, number: str) -> str:
    """Stable key for a printed card, e.g. card_key("SV1", "025/198") == "sv1-25".

    Sources disagree on formatting: pokemontcg.io uses "25", Cardmarket-style
    listings use "025/198", trainer gallery cards use "TG12/TG30". The key keeps
    only the card's own number, lowercased, with numeric parts de-padded.
    """
    set_part = set_code.strip().lower()
    if not set_part:
        raise ValueError("empty set code")
    num = number.strip().split("/")[0].strip().lower()
    if not num:
        raise ValueError(f"empty card number for set {set_code!r}")
    if num.isdigit():
        num = str(int(num))
    return f"{set_part}-{num}"
