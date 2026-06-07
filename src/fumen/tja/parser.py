"""TJA file parser."""

from __future__ import annotations

from pathlib import Path

from fumen.model import BranchPath, COURSE_NAME_TO_ID, Course, Measure, Song, TimelineEvent
from fumen.tja.branch import BranchState
from fumen.tja.encoding import read_tja_text
from fumen.tja.lexer import COMMAND_RE, HEADER_RE, INLINE_COMMAND_RE, normalize_lines
from fumen.tja.notes import finalize_course_notes
from fumen.tja.prune import strip_trailing_padding_measures


class ParseError(Exception):
    def __init__(self, message: str, line: int | None = None):
        self.line = line
        super().__init__(f"Line {line}: {message}" if line else message)


def _parse_int_list(value: str) -> list[int]:
    parts = [p.strip() for p in value.split(",") if p.strip()]
    result: list[int] = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            pass
    return result


def _parse_header_key(key: str) -> str:
    return key.upper()


class _CourseBuilder:
    def __init__(self, course_id: int) -> None:
        self.course_id = course_id
        self.metadata: dict[str, str] = {}
        self.balloon_counts: list[int] = []
        self.balloon_nor: list[int] = []
        self.balloon_exp: list[int] = []
        self.balloon_mas: list[int] = []
        self.measures: list[Measure] = []
        self.in_chart = False
        self.measure_index = 0
        self.current_bpm: float = 120.0
        self.gogo = False
        self.gogo_start_slot: int | None = None
        self.gogo_end_slot: int | None = None
        self.show_barline = True
        self.pending_slots: list[str] = []
        self.pending_events: list[TimelineEvent] = []
        self.branch = BranchState()

    def set_meta(self, key: str, value: str) -> None:
        k = _parse_header_key(key)
        self.metadata[k] = value
        if k == "BALLOON":
            self.balloon_counts = _parse_int_list(value)
            self.balloon_queue = list(self.balloon_counts)
        elif k == "BALLOONNOR":
            self.balloon_nor = _parse_int_list(value)
        elif k == "BALLOONEXP":
            self.balloon_exp = _parse_int_list(value)
        elif k == "BALLOONMAS":
            self.balloon_mas = _parse_int_list(value)
        elif k == "COURSE":
            try:
                self.course_id = int(value.strip())
            except ValueError:
                pass
        elif k == "LEVEL":
            pass

    def balloon_list(self, branch: BranchPath) -> list[int]:
        if branch == BranchPath.ADVANCED and self.balloon_exp:
            return list(self.balloon_exp)
        if branch == BranchPath.MASTER and self.balloon_mas:
            return list(self.balloon_mas)
        if self.balloon_nor:
            return list(self.balloon_nor)
        return list(self.balloon_counts)

    def flush_measure(self, branch: BranchPath) -> None:
        if not self.pending_slots and not self.pending_events:
            return
        self.measure_index += 1
        has_gogo = self.gogo or self.gogo_start_slot is not None
        if has_gogo and self.pending_slots:
            end_slot = self.gogo_end_slot
            if end_slot is None:
                end_slot = len(self.pending_slots) - 1
            start_slot = self.gogo_start_slot if self.gogo_start_slot is not None else 0
        else:
            start_slot = None
            end_slot = None
        m = Measure(
            index=self.measure_index,
            slots=list(self.pending_slots),
            gogo=has_gogo,
            gogo_start_slot=start_slot,
            gogo_end_slot=end_slot,
            show_barline=self.show_barline,
            events=list(self.pending_events),
            bpm=self.current_bpm,
        )
        include = self.branch.should_include_measure()
        if include:
            self.measures.append(m)
        else:
            # Still consume balloon slots from skipped path content
            bl = self.balloon_list(branch)
            for ch in self.pending_slots:
                if ch in "79" and bl:
                    bl.pop(0)

        self.pending_slots = []
        self.pending_events = []
        self.gogo_start_slot = None
        self.gogo_end_slot = None

    def handle_command(self, name: str, value: str | None, branch: BranchPath) -> None:
        upper = name.upper()
        if self.branch.handle_command(upper, value):
            return

        event = TimelineEvent(slot=len(self.pending_slots), name=upper, value=value)

        if upper == "START":
            self.in_chart = True
            return
        if upper == "END":
            self.flush_measure(branch)
            self.in_chart = False
            return
        if not self.in_chart:
            return

        if upper == "GOGOSTART":
            self.gogo = True
            self.gogo_start_slot = len(self.pending_slots)
            self.pending_events.append(event)
            return
        if upper == "GOGOEND":
            if self.gogo_start_slot is not None and self.pending_slots:
                self.gogo_end_slot = len(self.pending_slots) - 1
            self.gogo = False
            self.pending_events.append(event)
            return
        if upper == "BPMCHANGE" and value:
            try:
                self.current_bpm = float(value.strip())
            except ValueError:
                pass
            self.pending_events.append(event)
            return
        if upper == "BARLINEOFF":
            self.show_barline = False
            self.pending_events.append(event)
            return
        if upper == "BARLINEON":
            self.show_barline = True
            self.pending_events.append(event)
            return
        if upper in ("SCROLL", "HSPEED", "HBSCROLL", "BMSCROLL", "LYRIC"):
            self.pending_events.append(event)
            return
        if upper == "MEASURE":
            self.pending_events.append(event)
            return
        if upper == "DELAY":
            self.pending_events.append(event)
            return

        # Command breaks measure — flush first
        self.flush_measure(branch)
        self.pending_events.append(
            TimelineEvent(slot=0, name=upper, value=value)
        )

    def handle_measure_line(self, line: str, branch: BranchPath) -> None:
        """Parse a chart line that may contain digits and inline commands."""
        i = 0
        while i < len(line):
            if line[i] == "#":
                rest = line[i:]
                m = INLINE_COMMAND_RE.match(rest)
                if m:
                    name = m.group(1)
                    value = m.group(2)
                    self.handle_command(name, value, branch)
                    consumed = len(m.group(0))
                    i += consumed
                    continue
                break
            if line[i] == ",":
                self.flush_measure(branch)
                i += 1
                continue
            ch = line[i]
            if ch.upper() in "0123456789ABCDEF":
                self.pending_slots.append(ch.upper() if ch.isalpha() else ch)
            i += 1
        if line.rstrip().endswith(","):
            self.flush_measure(branch)

    def build(self, branch: BranchPath) -> Course:
        if self.in_chart:
            self.flush_measure(branch)
        try:
            level = int(self.metadata.get("LEVEL", "1"))
        except ValueError:
            level = 1
        course = Course(
            course_id=self.course_id,
            level=level,
            metadata=dict(self.metadata),
            balloon_counts=list(self.balloon_counts),
            balloon_nor=list(self.balloon_nor),
            balloon_exp=list(self.balloon_exp),
            balloon_mas=list(self.balloon_mas),
            measures=self.measures,
        )
        finalize_course_notes(course, course.balloon_list_for_branch(branch))
        strip_trailing_padding_measures(course)
        return course


def parse_tja(
    path: str | Path,
    *,
    course: str | int = 0,
    branch: BranchPath | str = BranchPath.NORMAL,
) -> tuple[Song, Course]:
    if isinstance(branch, str):
        branch = BranchPath(branch.lower())
    text = read_tja_text(path)
    lines = normalize_lines(text)

    song = Song(source_path=str(path))
    builders: list[_CourseBuilder] = []
    current: _CourseBuilder | None = None
    global_bpm = 120.0

    for lineno, line in lines:
        if line.startswith("#"):
            m = COMMAND_RE.match(line)
            if not m:
                raise ParseError(f"Invalid command: {line}", lineno)
            name = m.group(1)
            value = m.group(2)
            upper = name.upper()
            if upper == "START":
                if current is None:
                    current = _CourseBuilder(course_id=0)
                    builders.append(current)
                current.in_chart = True
                current.branch.apply_selected_branch(branch)
                current.current_bpm = global_bpm
                continue
            if upper == "END":
                if current:
                    current.handle_command(name, value, branch)
                continue
            if current and current.in_chart:
                if line.endswith(",") or any(c in line for c in "0123456789"):
                    current.handle_measure_line(line, branch)
                else:
                    current.handle_command(name, value, branch)
            continue

        hm = HEADER_RE.match(line)
        if hm:
            key, value = hm.group(1), hm.group(2).strip()
            k = _parse_header_key(key)
            if k == "COURSE":
                if value.isdigit():
                    cid = int(value)
                else:
                    cid = COURSE_NAME_TO_ID.get(value.lower(), 0)
                current = _CourseBuilder(course_id=cid)
                current.metadata["COURSE"] = value
                builders.append(current)
            elif current is not None and current.in_chart:
                pass
            elif current is not None:
                current.set_meta(key, value)
            else:
                song.metadata[k] = value
                if k == "BPM":
                    try:
                        global_bpm = float(value)
                    except ValueError:
                        pass
            if current is not None and k != "COURSE":
                if not current.in_chart or k in (
                    "LEVEL",
                    "BALLOON",
                    "BALLOONNOR",
                    "BALLOONEXP",
                    "BALLOONMAS",
                    "SCOREINIT",
                    "SCOREDIFF",
                    "NOTESDESIGNER0",
                    "NOTESDESIGNER1",
                    "NOTESDESIGNER2",
                    "NOTESDESIGNER3",
                    "NOTESDESIGNER4",
                ):
                    current.set_meta(key, value)
            continue

        if current and current.in_chart:
            current.handle_measure_line(line, branch)
        elif current is None:
            raise ParseError("Chart data outside of course", lineno)

    courses = [b.build(branch) for b in builders]
    song.courses = courses

    selected = song.get_course(course)
    if selected is None:
        raise ParseError(f"Course not found: {course!r}")

    return song, selected
