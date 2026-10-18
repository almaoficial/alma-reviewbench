from __future__ import annotations

from dataclasses import dataclass
import re

from .diff_parser import DiffIndex, DiffLine


@dataclass(frozen=True)
class Candidate:
    rule_id: str
    claim_type: str
    file: str
    start_line: int
    end_line: int
    message: str
    evidence_text: tuple[str, ...]
    severity_hint: str
    category_hint: str
    producer: str = "alma-base-reviewer"


_SQL_RE = re.compile(r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b", re.I)
_UNSAFE_SQL_RE = re.compile(
    r"(?:\bf[\"']|\bf'''|\.format\s*\(|%\s*\(|[\"']\s*\+|\+\s*[A-Za-z_][\w.\[\]]*)",
    re.I,
)
_SECRET_NAME_RE = re.compile(r"(api[_-]?key|(?:access[_-]?|auth[_-]?)?token|password|passwd|secret)", re.I)
_SECRET_LITERAL_RE = re.compile(
    r"^\s*[A-Za-z_][\w.]*\s*=\s*([\"'])(?P<value>[^\"']{6,})\1\s*(?:#.*)?$"
)
_SECRET_ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z_][\w.]*)\s*=\s*(.+)$")
_MUTABLE_DEFAULT_RE = re.compile(r"\bdef\s+\w+\s*\([^)]*=\s*(\[\]|\{\}|set\(\))")


def _is_unsafe_sql(text: str) -> bool:
    return bool(_SQL_RE.search(text) and _UNSAFE_SQL_RE.search(text))


class BaseReviewer:
    """A deterministic stand-in reviewer used for US$0 local validation.

    It intentionally contains a few over-broad heuristics.  Those heuristics
    are useful fixtures: they generate plausible but unsupported candidates
    that the ALMA gate must reject instead of laundering into findings.
    """

    name = "alma-base-reviewer"

    def review(self, diff: DiffIndex) -> list[Candidate]:
        candidates: list[Candidate] = []
        seen: set[tuple[str, str, int, int]] = set()

        def add(candidate: Candidate) -> None:
            key = (
                candidate.rule_id,
                candidate.file,
                candidate.start_line,
                candidate.end_line,
            )
            if key not in seen:
                seen.add(key)
                candidates.append(candidate)

        for file_diff in diff.files.values():
            added = file_diff.added_lines()
            file_has_sql = any(_SQL_RE.search(line.text) for line in added)
            race_candidate_emitted = False

            for line in added:
                text = line.text
                stripped = text.strip()

                if _is_unsafe_sql(text):
                    add(
                        Candidate(
                            "unsafe_sql_construction",
                            "sql_injection",
                            line.file,
                            line.line_number,
                            line.line_number,
                            "SQL injection risk: the query is built with string interpolation or concatenation, so untrusted values can change the SQL statement instead of being bound as parameters.",
                            (text,),
                            "high",
                            "security",
                        )
                    )
                elif file_has_sql and ".execute(" in text and re.search(r"\.execute\([^)]*,\s*\(", text):
                    # Over-broad by design: an execute call near SQL text is
                    # not evidence that this call site is injectable.
                    add(
                        Candidate(
                            "possible_sql_injection_unverified_call_site",
                            "sql_injection",
                            line.file,
                            line.line_number,
                            line.line_number,
                            "Possible SQL injection: this execute call is near SQL construction, so its query may be injectable.",
                            (text,),
                            "high",
                            "security",
                        )
                    )

                if (
                    "os.system(" in text
                    or re.search(r"\b(?:eval|exec)\s*\(", text)
                    or ("subprocess" in text and "shell=True" in text)
                    or "shell=True" in text
                ):
                    add(
                        Candidate(
                            "unsafe_command_execution",
                            "command_execution",
                            line.file,
                            line.line_number,
                            line.line_number,
                            "Command execution risk: this code evaluates code or invokes a shell in a way that can turn data into executable commands.",
                            (text,),
                            "high",
                            "security",
                        )
                    )

                if "verify=False" in text.replace(" ", ""):
                    add(
                        Candidate(
                            "tls_verification_disabled",
                            "tls_verification_disabled",
                            line.file,
                            line.line_number,
                            line.line_number,
                            "TLS verification is disabled with verify=False, so the connection can accept an invalid or attacker-controlled certificate.",
                            (text,),
                            "high",
                            "security",
                        )
                    )

                if "pickle.loads(" in text or "yaml.load(" in text and "SafeLoader" not in text:
                    add(
                        Candidate(
                            "unsafe_deserialization",
                            "unsafe_deserialization",
                            line.file,
                            line.line_number,
                            line.line_number,
                            "Unsafe deserialization: loading untrusted data with this API can execute attacker-controlled content instead of only constructing data objects.",
                            (text,),
                            "high",
                            "security",
                        )
                    )

                secret_literal = _SECRET_LITERAL_RE.match(text)
                assignment = _SECRET_ASSIGNMENT_RE.match(text)
                if secret_literal and _SECRET_NAME_RE.search(text.split("=", 1)[0]):
                    add(
                        Candidate(
                            "hardcoded_secret_literal",
                            "hardcoded_secret",
                            line.file,
                            line.line_number,
                            line.line_number,
                            "Hardcoded credential: a secret value is embedded directly in source code, where it can leak through the repository and cannot be rotated independently.",
                            (text,),
                            "high",
                            "security",
                        )
                    )
                elif assignment and _SECRET_NAME_RE.search(assignment.group(1)):
                    rhs = assignment.group(2)
                    if "os.getenv(" in rhs or "os.environ" in rhs:
                        # Over-broad by design: a secret-looking variable name
                        # does not prove that the value is hardcoded.
                        add(
                            Candidate(
                                "possible_hardcoded_secret_from_name",
                                "hardcoded_secret",
                                line.file,
                                line.line_number,
                                line.line_number,
                                "Possible hardcoded credential: this assignment uses a credential-like variable name, so the value may be embedded in source code.",
                                (text,),
                                "high",
                                "security",
                            )
                        )

                if _MUTABLE_DEFAULT_RE.search(text):
                    add(
                        Candidate(
                            "mutable_default_argument",
                            "mutable_default",
                            line.file,
                            line.line_number,
                            line.line_number,
                            "Mutable default argument: the default object is created once and shared across calls, so mutations can leak state between invocations.",
                            (text,),
                            "medium",
                            "correctness",
                        )
                    )

                if not race_candidate_emitted and stripped.startswith("def ") and "cache" in text.lower():
                    # Over-broad by design: the word "cache" alone is not
                    # evidence of a race condition.
                    add(
                        Candidate(
                            "possible_cache_race_condition",
                            "race_condition",
                            line.file,
                            line.line_number,
                            line.line_number,
                            "Possible race condition: this cache-related function may access shared state concurrently without synchronization.",
                            (text,),
                            "medium",
                            "reliability",
                        )
                    )
                    race_candidate_emitted = True

            # A bare ``except:`` is only treated as a candidate when the
            # silencing ``pass`` is also visible in the diff.
            for line in added:
                if line.text.strip() != "except:":
                    continue
                for following_number in range(line.line_number + 1, line.line_number + 4):
                    following = diff.get_line(line.file, following_number)
                    if following is not None and following.text.strip() == "pass":
                        add(
                            Candidate(
                                "bare_except_silences_errors",
                                "silenced_bare_except",
                                line.file,
                                line.line_number,
                                following.line_number,
                                "Errors are silently discarded: the bare except catches every exception and the handler only passes, hiding failures and making defects difficult to diagnose.",
                                (line.text, following.text),
                                "medium",
                                "reliability",
                            )
                        )
                        break

        return candidates
