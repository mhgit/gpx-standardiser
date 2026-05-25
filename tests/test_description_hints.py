"""Description hint heuristic coverage."""

from gpx_standardiser.description_hints import description_hint_from_original


def test_hint_hadlow() -> None:
    assert description_hint_from_original("Hadlow_45_miles.gpx") == "Hadlow"


def test_hint_babylon() -> None:
    assert description_hint_from_original("Babylon__Duddleswell_48m.gpx") == "Babylon-Duddleswell"


def test_hint_legacy_circumflex_suffix_prefers_suffix() -> None:
    stem = "67mls_107km-547mtrs_1794ft^Staplehurst.gpx"
    assert description_hint_from_original(stem) == "Staplehurst"


def test_hint_canonical_at_suffix_prefers_suffix() -> None:
    stem = "67mls_107km-547mtrs_1794ft@Staplehurst.gpx"
    assert description_hint_from_original(stem) == "Staplehurst"


def test_hint_strips_ability_tokens() -> None:
    fname = "T4-T5_Red_Barn-Charlwood-Brockham-Boxhill-Red_Barn_82km.gpx"
    hint = description_hint_from_original(fname)
    assert hint == "Red-Barn-Charlwood-Brockham-Boxhill-Red-Barn"


def test_hint_pure_numbers_returns_blank() -> None:
    assert description_hint_from_original("107_108_109.gpx") == ""


def test_hint_penshurst() -> None:
    assert description_hint_from_original("Penshurst_-_37.gpx") == "Penshurst"


def test_hint_strips_leading_joining_to() -> None:
    assert description_hint_from_original("To-Ardingly-Roost-Cafe.gpx") == "Ardingly-Roost-Cafe"


def test_hint_strips_occ_prefix_and_infix_to() -> None:
    # OCC (Club filename prefix from config.yaml join_words) plus joiner "to"
    assert description_hint_from_original("OCC_to_Tea_Pot_60_miles.gpx") == "Tea-Pot"


def test_hint_strips_joining_after_at_suffix() -> None:
    assert description_hint_from_original("10km@To-Tea-Shop.gpx") == "Tea-Shop"
