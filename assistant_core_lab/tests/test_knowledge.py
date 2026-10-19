import pytest
from pathlib import Path
from assistant_core.knowledge import OfficeDirectory, Handbook
from assistant_core.errors import DataError


def test_office_directory_from_csv_loads_all_offices():
    offices = OfficeDirectory.from_csv(Path("data/offices.csv"))
    assert len(offices._offices) == 4


def test_office_directory_from_csv_missing_file_raises_dataerror():
    with pytest.raises(DataError):
        OfficeDirectory.from_csv(Path("nonexistent.csv"))


def test_office_directory_names_returns_all_names():
    offices = OfficeDirectory.from_csv(Path("data/offices.csv"))
    assert len(offices.names) == 4


def test_office_find_returns_office_when_name_in_text():
    offices = OfficeDirectory.from_csv(Path("data/offices.csv"))
    result = offices.find("where is the library")
    assert result is not None
    assert result.name == "Library"


def test_office_find_returns_none_when_not_found():
    offices = OfficeDirectory.from_csv(Path("data/offices.csv"))
    result = offices.find("unknown place")
    assert result is None


def test_handbook_from_json_loads_all_rules():
    handbook = Handbook.from_json(Path("data/handbook.json"))
    assert len(handbook._rules) == 5


def test_handbook_from_json_missing_file_raises_dataerror():
    with pytest.raises(DataError):
        Handbook.from_json(Path("nonexistent.json"))


def test_handbook_search_returns_rule_when_keyword_match():
    handbook = Handbook.from_json(Path("data/handbook.json"))
    rule = handbook.search("retake credits")
    assert rule is not None
    assert rule.id == "H26-4.2"


def test_handbook_search_returns_none_when_no_match():
    handbook = Handbook.from_json(Path("data/handbook.json"))
    rule = handbook.search("xyz unknown topic")
    assert rule is None