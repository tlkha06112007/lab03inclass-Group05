from pathlib import Path

import pytest

from assistant_core.errors import DataError
from assistant_core.knowledge import Handbook, Office, OfficeDirectory

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OFFICES_CSV = DATA_DIR / "offices.csv"
HANDBOOK_JSON = DATA_DIR / "handbook.json"


def test_office_directory_from_csv_loads_all_offices():
    offices = OfficeDirectory.from_csv(OFFICES_CSV)
    assert len(offices.names) == 4


def test_office_directory_from_csv_missing_file_raises_dataerror():
    with pytest.raises(DataError):
        OfficeDirectory.from_csv(Path("nonexistent.csv"))


def test_office_directory_from_csv_missing_columns_raises_dataerror(tmp_path):
    bad_csv = tmp_path / "bad_columns.csv"
    bad_csv.write_text("name,room\nLibrary,B.201\n", encoding="utf-8")
    with pytest.raises(DataError):
        OfficeDirectory.from_csv(bad_csv)


def test_office_directory_from_csv_invalid_encoding_raises_dataerror(tmp_path):
    bad_csv = tmp_path / "bad_encoding.csv"
    bad_csv.write_bytes(b"\xff\xfe\x00\x00not_utf8")
    with pytest.raises(DataError):
        OfficeDirectory.from_csv(bad_csv)


def test_office_directory_names_returns_all_names():
    offices = OfficeDirectory.from_csv(OFFICES_CSV)
    assert len(offices.names) == 4


def test_office_find_returns_office_when_name_in_text():
    offices = OfficeDirectory.from_csv(OFFICES_CSV)
    result = offices.find("where is the library")
    assert result is not None
    assert result.name == "Library"


def test_office_find_returns_none_when_not_found():
    offices = OfficeDirectory.from_csv(OFFICES_CSV)
    result = offices.find("unknown place")
    assert result is None


def test_office_find_selects_longest_matching_name():
    offices = OfficeDirectory({
        "office": Office("Office", "101", "8-17"),
        "training office": Office("Training Office", "I.101", "7:30-16:30"),
    })
    result = offices.find("where is the training office?")
    assert result is not None
    assert result.name == "Training Office"


def test_handbook_from_json_loads_all_rules():
    handbook = Handbook.from_json(HANDBOOK_JSON)
    assert handbook.search("retake credits") is not None
    assert handbook.search("thesis") is not None


def test_handbook_from_json_missing_file_raises_dataerror():
    with pytest.raises(DataError):
        Handbook.from_json(Path("nonexistent.json"))


def test_handbook_from_json_invalid_json_raises_dataerror(tmp_path):
    bad_json = tmp_path / "invalid.json"
    bad_json.write_text("{not a valid json", encoding="utf-8")
    with pytest.raises(DataError):
        Handbook.from_json(bad_json)


def test_handbook_from_json_not_a_list_raises_dataerror(tmp_path):
    bad_json = tmp_path / "not_list.json"
    bad_json.write_text('{"id": "H1", "title": "Rule", "text": "text"}', encoding="utf-8")
    with pytest.raises(DataError):
        Handbook.from_json(bad_json)


def test_handbook_from_json_missing_keys_raises_dataerror(tmp_path):
    bad_json = tmp_path / "missing_keys.json"
    bad_json.write_text('[{"id": "H1", "title": "No text"}]', encoding="utf-8")
    with pytest.raises(DataError):
        Handbook.from_json(bad_json)


def test_handbook_search_returns_rule_when_keyword_match():
    handbook = Handbook.from_json(HANDBOOK_JSON)
    rule = handbook.search("retake credits")
    assert rule is not None
    assert rule.id == "H26-4.2"


def test_handbook_search_returns_none_when_no_match():
    handbook = Handbook.from_json(HANDBOOK_JSON)
    rule = handbook.search("xyz unknown topic")
    assert rule is None


@pytest.mark.parametrize("query", ["", "   ", "a", "the"])
def test_handbook_search_empty_or_short_query_returns_none(query):
    handbook = Handbook.from_json(HANDBOOK_JSON)
    assert handbook.search(query) is None