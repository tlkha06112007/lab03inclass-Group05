from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from assistant_core.errors import DataError


@dataclass(frozen=True)
class Office:
    name: str
    room: str
    hours: str


class OfficeDirectory:
    def __init__(self, offices: dict[str, Office]):
        self._offices = offices

    @classmethod
    def from_csv(cls, path: Path) -> OfficeDirectory:
        try:
            with path.open(encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                required = {"name", "room", "hours"}
                if reader.fieldnames is None or not required.issubset(reader.fieldnames):
                    raise DataError(f"missing required columns in {path}")
                rows = list(reader)
                return cls({r["name"].lower(): Office(r["name"], r["room"], r["hours"]) for r in rows})
        except FileNotFoundError as exc:
            raise DataError(f"office file not found: {path}") from exc
        except (csv.Error, UnicodeDecodeError) as exc:
            raise DataError(f"malformed office file: {path}") from exc

    @property
    def names(self) -> set[str]:
        return set(self._offices)

    def find(self, text: str) -> Office | None:
        t = text.lower()
        matches = [o for name, o in self._offices.items() if name in t]
        if not matches:
            return None
        return max(matches, key=lambda o: len(o.name))


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    text: str


class Handbook:
    def __init__(self, rules: list[Rule]):
        self._rules = rules

    @classmethod
    def from_json(cls, path: Path) -> Handbook:
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as exc:
            raise DataError(f"handbook file not found: {path}") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise DataError(f"malformed handbook file: {path}") from exc

        if not isinstance(data, list):
            raise DataError(f"malformed handbook file (expected a list): {path}")

        try:
            return cls([Rule(r["id"], r["title"], r["text"]) for r in data])
        except (KeyError, TypeError) as exc:
            raise DataError(f"missing required rule keys in {path}") from exc

    def search(self, query: str) -> Rule | None:
        q = query.lower().strip()
        if not q:
            return None

        # Direct substring match in text or title (skip short queries < 4 chars)
        if len(q) >= 4:
            for r in self._rules:
                if q in r.text.lower() or q in r.title.lower():
                    return r

        # Keyword overlap score for words with length > 3
        words = [w for w in q.split() if len(w) > 3]
        if not words:
            return None

        best_rule = None
        best_score = 0
        for r in self._rules:
            content = f"{r.title} {r.text}".lower()
            score = sum(1 for w in words if w in content)
            if score > best_score:
                best_score = score
                best_rule = r
        return best_rule if best_score > 0 else None
