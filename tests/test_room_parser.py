from app.utils.room_parser import parse_room_name, format_room_name


def test_parse_room_name_single_digit_floor():
    parsed = parse_room_name("106-B blok")
    assert parsed["floor_number"] == 1
    assert parsed["room_number"] == "06"
    assert parsed["building"] == "B"


def test_parse_room_name_two_digit_floor_and_lowercase_block():
    parsed = parse_room_name("1006-b blok")
    assert parsed["floor_number"] == 10
    assert parsed["room_number"] == "06"
    assert parsed["building"] == "B"


def test_parse_room_name_accepts_spaces_and_block_variant():
    parsed = parse_room_name("  1106 -  c  block ")
    assert parsed["floor_number"] == 11
    assert parsed["room_number"] == "06"
    assert parsed["building"] == "C"


def test_format_room_name_normalizes_building_to_uppercase():
    assert format_room_name(10, "06", "b") == "1006-B blok"

