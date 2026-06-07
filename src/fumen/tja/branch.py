"""Branch path state machine for TJA charts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from fumen.model import BranchPath


class BranchMode(Enum):
    NONE = auto()
    SECTION = auto()
    BRANCHING = auto()
    LEVELHOLD = auto()


@dataclass
class BranchState:
    """Tracks which chart path is active during parse."""

    selected: BranchPath = BranchPath.NORMAL
    mode: BranchMode = BranchMode.NONE
    # During branching: which paths are being written
    active_paths: set[BranchPath] = field(default_factory=lambda: {BranchPath.NORMAL})
    # Skip measure content but still count balloons
    skip_content: bool = False
    # After #BRANCHSTART, next path markers select branches
    branch_started: bool = False
    balloon_skip_only: bool = False

    def reset_section(self) -> None:
        self.mode = BranchMode.SECTION
        self.active_paths = {BranchPath.NORMAL}
        self.skip_content = False
        self.branch_started = False

    def start_branch(self) -> None:
        self.mode = BranchMode.BRANCHING
        self.branch_started = True
        self.active_paths = set()
        self.skip_content = True

    def end_branch(self) -> None:
        self.mode = BranchMode.NONE
        self.branch_started = False
        if not self.active_paths:
            self.active_paths = {BranchPath.NORMAL}
        self.skip_content = False

    def set_path_marker(self, marker: str) -> None:
        path_map = {
            "N": BranchPath.NORMAL,
            "NORMAL": BranchPath.NORMAL,
            "E": BranchPath.ADVANCED,
            "ADVANCED": BranchPath.ADVANCED,
            "R": BranchPath.MASTER,
            "MASTER": BranchPath.MASTER,
        }
        path = path_map.get(marker.upper())
        if path is None:
            return
        if self.branch_started and not self.active_paths:
            self.active_paths = {path}
            self.skip_content = path != self.selected
        elif self.mode == BranchMode.BRANCHING:
            self.active_paths.add(path)
            self.skip_content = self.selected not in self.active_paths

    def should_include_measure(self) -> bool:
        if self.mode == BranchMode.NONE:
            return True
        if self.balloon_skip_only:
            return False
        if not self.active_paths:
            return self.selected == BranchPath.NORMAL
        return self.selected in self.active_paths and not self.skip_content

    def should_count_balloon(self) -> bool:
        """Balloon metadata advances even on skipped paths."""
        return True

    def handle_command(self, name: str, value: str | None) -> bool:
        """
        Process branch-related command.
        Returns True if command was consumed.
        """
        upper = name.upper()
        if upper == "SECTION":
            self.reset_section()
            return True
        if upper == "BRANCHSTART":
            self.start_branch()
            return True
        if upper == "BRANCHEND":
            self.end_branch()
            return True
        if upper == "LEVELHOLD":
            self.mode = BranchMode.LEVELHOLD
            return True
        if upper == "LEVELHOLDEND":
            self.mode = BranchMode.BRANCHING if self.branch_started else BranchMode.NONE
            return True
        if upper in ("N", "NORMAL"):
            self.set_path_marker("N")
            return True
        if upper in ("E", "ADVANCED"):
            self.set_path_marker("E")
            return True
        if upper in ("R", "MASTER"):
            self.set_path_marker("R")
            return True
        if upper in ("DON", "KA"):
            return True
        return False

    def apply_selected_branch(self, branch: BranchPath) -> None:
        self.selected = branch
        if self.active_paths:
            self.skip_content = branch not in self.active_paths
