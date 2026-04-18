from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Extension:
    """Declares a single extension to apply."""
    type: str           # "git" or "file"
    name: str
    # git-only
    repo: Optional[str] = None
    ref: Optional[str] = None
    # file-only
    path: Optional[str] = None


@dataclass
class ResolvedExtension:
    """An extension whose source has been fetched to a local directory."""
    name: str
    local_path: str     # absolute path to the extension root directory


@dataclass
class ElementChange:
    kind: str           # "new", "append", or "replace"
    element_type: str   # "enum", "struct", or "packet"
    identifier: str     # name (enum/struct) or "FamilyAction" (packet)


@dataclass
class MergeResult:
    extension_name: str
    changes: list[ElementChange] = field(default_factory=list)

    @property
    def new_count(self) -> int:
        return sum(1 for c in self.changes if c.kind == "new")

    @property
    def append_count(self) -> int:
        return sum(1 for c in self.changes if c.kind == "append")

    @property
    def replace_count(self) -> int:
        return sum(1 for c in self.changes if c.kind == "replace")

    def summary(self) -> str:
        parts = []
        if self.new_count:
            parts.append(f"{self.new_count} new")
        if self.append_count:
            parts.append(f"{self.append_count} appended")
        if self.replace_count:
            parts.append(f"{self.replace_count} replaced")
        return ", ".join(parts) if parts else "no changes"
