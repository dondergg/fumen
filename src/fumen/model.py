"""Chart data model for parsed TJA courses."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class NoteKind(Enum):
    DON = auto()
    KA = auto()
    BIG_DON = auto()
    BIG_KA = auto()
    ROLL = auto()
    BIG_ROLL = auto()
    BALLOON = auto()
    BIG_BALLOON = auto()


class BranchPath(Enum):
    NORMAL = "normal"
    ADVANCED = "advanced"
    MASTER = "master"


COURSE_NAMES: dict[int, str] = {
    0: "かんたん",
    1: "ふつう",
    2: "むずかしい",
    3: "おに",
    4: "裏",
}

COURSE_LABEL_JA: dict[str, str] = {
    "Easy": "かんたん",
    "Normal": "ふつう",
    "Hard": "むずかしい",
    "Oni": "おに",
    "Edit": "裏",
    "Ura": "裏",
}

COURSE_NAME_TO_ID: dict[str, int] = {
    "easy": 0,
    "normal": 1,
    "hard": 2,
    "oni": 3,
    "edit": 4,
    "ura": 4,
}

COURSE_ALIASES: dict[str, int] = {
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "easy": 0,
    "normal": 1,
    "hard": 2,
    "oni": 3,
    "ura": 4,
    "edit": 4,
    "かんたん": 0,
    "ふつう": 1,
    "むずかしい": 2,
    "おに": 3,
    "裏": 4,
    "kantan": 0,
    "futsuu": 1,
    "muzukashii": 2,
}


@dataclass
class SlotNote:
    """A hit note at a single slot index."""

    slot: int
    kind: NoteKind


@dataclass
class SpanNote:
    """Roll or balloon spanning slot range [start_slot, end_slot] within one measure."""

    start_slot: int
    end_slot: int
    kind: NoteKind
    balloon_hits: int | None = None
    continues_to_next: bool = False
    continues_from_prev: bool = False


@dataclass
class TimelineEvent:
    """Command at a slot boundary within a measure."""

    slot: int
    name: str
    value: str | None = None


@dataclass
class Measure:
    """One comma-terminated measure segment."""

    index: int  # 1-based display index
    slots: list[str]
    gogo: bool = False
    gogo_start_slot: int | None = None
    gogo_end_slot: int | None = None
    show_barline: bool = True
    events: list[TimelineEvent] = field(default_factory=list)
    hit_notes: list[SlotNote] = field(default_factory=list)
    span_notes: list[SpanNote] = field(default_factory=list)
    bpm: float | None = None  # BPM active at start of this measure


@dataclass
class Course:
    """One difficulty course (#START … #END)."""

    course_id: int
    level: int = 1
    metadata: dict[str, str] = field(default_factory=dict)
    balloon_counts: list[int] = field(default_factory=list)
    balloon_nor: list[int] = field(default_factory=list)
    balloon_exp: list[int] = field(default_factory=list)
    balloon_mas: list[int] = field(default_factory=list)
    measures: list[Measure] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        return COURSE_NAMES.get(self.course_id, str(self.course_id))

    def balloon_list_for_branch(self, branch: BranchPath) -> list[int]:
        if branch == BranchPath.ADVANCED and self.balloon_exp:
            return self.balloon_exp
        if branch == BranchPath.MASTER and self.balloon_mas:
            return self.balloon_mas
        if self.balloon_nor:
            return self.balloon_nor
        return self.balloon_counts


@dataclass
class Song:
    """Parsed TJA file."""

    metadata: dict[str, str] = field(default_factory=dict)
    courses: list[Course] = field(default_factory=list)
    source_path: str | None = None

    @property
    def title(self) -> str:
        return self.metadata.get("TITLE", "Unknown")

    @property
    def subtitle(self) -> str:
        sub = self.metadata.get("SUBTITLE", "")
        if sub.startswith("--") or sub.startswith("++"):
            return sub[2:].strip()
        return sub

    @property
    def bpm(self) -> float:
        try:
            return float(self.metadata.get("BPM", "120"))
        except ValueError:
            return 120.0

    def get_course(self, selector: str | int) -> Course | None:
        if isinstance(selector, int):
            if 0 <= selector < len(self.courses):
                return self.courses[selector]
            for c in self.courses:
                if c.course_id == selector:
                    return c
            return None
        key = str(selector).strip()
        key_lower = key.lower()
        if key_lower.isdigit():
            idx = int(key_lower)
            if 0 <= idx < len(self.courses):
                return self.courses[idx]
            return self.get_course(idx)
        for c in self.courses:
            if c.metadata.get("COURSE", "").lower() == key_lower:
                return c
        if key_lower in COURSE_ALIASES:
            cid = COURSE_ALIASES[key_lower]
            for c in self.courses:
                if c.course_id == cid:
                    return c
            if 0 <= cid < len(self.courses):
                return self.courses[cid]
        for c in self.courses:
            if COURSE_NAMES.get(c.course_id, "").lower() == key_lower:
                return c
        if key in COURSE_LABEL_JA:
            for c in self.courses:
                if c.metadata.get("COURSE", "") == key:
                    return c
        return None
