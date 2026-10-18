from __future__ import annotations

from dataclasses import dataclass, field
import re


_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class DiffLine:
    """One line as it exists at the PR head and appears in the diff."""

    file: str
    line_number: int
    text: str
    kind: str  # "added" or "context"


@dataclass
class FileDiff:
    path: str
    lines: dict[int, DiffLine] = field(default_factory=dict)

    def add(self, line: DiffLine) -> None:
        self.lines[line.line_number] = line

    def sorted_lines(self) -> list[DiffLine]:
        return [self.lines[number] for number in sorted(self.lines)]

    def added_lines(self) -> list[DiffLine]:
        return [line for line in self.sorted_lines() if line.kind == "added"]


@dataclass
class DiffIndex:
    files: dict[str, FileDiff] = field(default_factory=dict)

    def get_line(self, path: str, line_number: int) -> DiffLine | None:
        file_diff = self.files.get(path)
        if file_diff is None:
            return None
        return file_diff.lines.get(line_number)

    def file(self, path: str) -> FileDiff | None:
        return self.files.get(path)


def _clean_diff_path(raw: str) -> str | None:
    path = raw.strip().strip('"')
    if path == "/dev/null":
        return None
    if len(path) >= 2 and path[0] in {"a", "b"} and path[1] == "/":
        path = path[2:]
    return path


def parse_unified_diff(diff_text: str) -> DiffIndex:
    """Parse a unified diff and index every context/added line by head number.

    Deleted lines have no head line number and are not indexed.  The parser is
    intentionally small, but follows the standard hunk accounting used by
    ``git diff`` and by ReviewBench's ``diff.patch`` artifact.
    """

    index = DiffIndex()
    current_file: FileDiff | None = None
    new_line_number: int | None = None

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            current_file = None
            new_line_number = None
            continue

        if raw_line.startswith("+++ "):
            path = _clean_diff_path(raw_line[4:])
            if path is None:
                current_file = None
            else:
                current_file = index.files.setdefault(path, FileDiff(path=path))
            new_line_number = None
            continue

        if raw_line.startswith("--- "):
            continue

        hunk = _HUNK_RE.match(raw_line)
        if hunk:
            new_line_number = int(hunk.group(1))
            continue

        if current_file is None or new_line_number is None:
            continue
        if raw_line.startswith("\\"):
            continue

        if raw_line == "":
            prefix, text = " ", ""
        else:
            prefix, text = raw_line[0], raw_line[1:]

        if prefix == "+":
            current_file.add(
                DiffLine(current_file.path, new_line_number, text, "added")
            )
            new_line_number += 1
        elif prefix == " ":
            current_file.add(
                DiffLine(current_file.path, new_line_number, text, "context")
            )
            new_line_number += 1
        elif prefix == "-":
            continue
        else:
            # A non-diff line terminates the current hunk for our purposes.
            new_line_number = None

    return index
