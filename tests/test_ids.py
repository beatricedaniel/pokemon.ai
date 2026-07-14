import pytest

from pokemon_tcg.ids import card_key


def test_plain_number():
    assert card_key("sv1", "25") == "sv1-25"


def test_cardmarket_style_denominator_dropped():
    assert card_key("SV1", "025/198") == "sv1-25"


def test_zero_padding_normalized():
    assert card_key("sv1", "025") == card_key("sv1", "25")


def test_trainer_gallery_number_kept_verbatim():
    assert card_key("SWSH9", "TG12/TG30") == "swsh9-tg12"


def test_whitespace_stripped():
    assert card_key(" sv1 ", " 25 ") == "sv1-25"


def test_empty_set_code_rejected():
    with pytest.raises(ValueError):
        card_key("  ", "25")


def test_empty_number_rejected():
    with pytest.raises(ValueError):
        card_key("sv1", "/198")
