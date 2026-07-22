import pytest

from pokemon_tcg.rarity import UNMAPPED_RARITY, normalize_rarity


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Common", "Common"),
        ("Uncommon", "Uncommon"),
        ("Rare", "Rare"),
        ("Rare Holo", "Rare Holo"),
        ("Holo Rare", "Rare Holo"),
        ("Rare Holo EX", "Ultra Rare"),
        ("Rare Holo GX", "Ultra Rare"),
        ("Rare Holo V", "Ultra Rare"),
        ("Rare Holo VMAX", "Ultra Rare"),
        ("Rare Ultra", "Ultra Rare"),
        ("Ultra Rare", "Ultra Rare"),
        ("Double Rare", "Double Rare"),
        ("Rare Secret", "Secret Rare"),
        ("Rare Rainbow", "Secret Rare"),
        ("Hyper Rare", "Secret Rare"),
        ("Illustration Rare", "Illustration Rare"),
        ("Special Illustration Rare", "Illustration Rare"),
        ("Promo", "Promo"),
    ],
)
def test_known_rarity_mapped(raw, expected):
    assert normalize_rarity(raw) == expected


def test_unknown_rarity_flagged_unmapped():
    assert normalize_rarity("Some Future Rarity Nobody Has Seen") == UNMAPPED_RARITY


def test_missing_rarity_flagged_unmapped():
    assert normalize_rarity(None) == UNMAPPED_RARITY
