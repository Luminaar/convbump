from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Collection, Dict, List, Optional, Tuple

from .git import Commit

BREAKING_CHANGE_IN_BODY = "BREAKING CHANGE:"
SUBJECT_REGEX = re.compile(
    r"""^
        (?:                         # Non-matchin group with commit type and optional scope
            (?P<type>[a-zA-Z]*?)    # Commit type (named group)
            (?:
                \(                  # Literal (
                    (?P<scope>.*)   # Scope (named group)
                \)                  # Literal )
            )?
        )
        (?P<breaking>!)?            # Breaking change mark (named group)
        :\s?                        # ':' follwed by any number of whitespace
        (?P<subject>.*)             # Rest of the subejct(named group)
        $
    """,
    re.VERBOSE,
)


class CommitType(Enum):
    FEAT = "feat"
    FIX = "fix"
    CHORE = "chore"
    DOCS = "docs"
    TEST = "test"
    REFACTOR = "refactor"
    STYLE = "style"
    BUILD = "build"
    CI = "ci"
    OTHER = "other"


def parse_subject(subject: str) -> Tuple[str, Optional[str], bool, str]:
    match = SUBJECT_REGEX.match(subject)
    if match:
        matched_dict = match.groupdict()
        if not matched_dict["subject"]:
            raise ValueError(f"Invalid conventional commit subejct: {subject}")

        commit_type = matched_dict["type"]
        is_breaking = bool(matched_dict.get("breaking", None))

        return (commit_type, matched_dict.get("scope"), is_breaking, matched_dict["subject"])
    else:
        raise ValueError(f"Invalid conventional commit subejct: {subject}")


@dataclass(frozen=True)
class ConventionalCommit:

    commit_type: CommitType
    scope: Optional[str]
    is_breaking: bool
    subject: str
    body: Optional[str]
    hash: str
    raw_subject: str

    @classmethod
    def from_git_commit(cls, git_commit: Commit) -> ConventionalCommit:
        raw_commit_type, scope, is_breaking, subject = parse_subject(git_commit.subject)

        try:
            commit_type = CommitType[raw_commit_type.upper()]
        except KeyError:
            commit_type = CommitType.OTHER

        if git_commit.body is not None and BREAKING_CHANGE_IN_BODY in git_commit.body:
            is_breaking = True

        return cls(
            commit_type=commit_type,
            scope=scope,
            is_breaking=is_breaking,
            subject=subject,
            body=git_commit.body or None,
            hash=git_commit.hash.decode()[:7],
            raw_subject=git_commit.subject,
        )

    def format(self) -> str:

        if self.scope:
            scope = f"(`{self.scope}`)"
        else:
            scope = ""

        if self.commit_type not in (CommitType.FEAT, CommitType.FIX):
            commit_type = f"{self.commit_type.value}{scope}: "
        else:
            if scope:
                commit_type = f"{scope} "
            else:
                commit_type = ""

        if self.is_breaking:
            breaking = "**BREAKING CHANGE** "
        else:
            breaking = ""

        return f"{breaking}{commit_type}{self.subject} ({self.hash})"


def format_changelog(commits: Collection[ConventionalCommit]) -> str:
    """Return a formatted changelog in Markdown format. Feature and fix commits
    are listed in a separate sections. Other commit types are grouped together
    in "Other" section."""

    commit_groups: Dict[CommitType, List[ConventionalCommit]] = defaultdict(list)

    for commit in commits:
        if commit.commit_type in (CommitType.FEAT, CommitType.FIX):
            commit_type = commit.commit_type
        else:
            commit_type = CommitType.OTHER

        commit_groups[commit_type].append(commit)

    lines = []

    for commit_type in CommitType:
        if commit_type in commit_groups:
            if commit_type == CommitType.FEAT:
                title = "Features"
            elif commit_type == CommitType.FIX:
                title = "Fixes"
            else:
                title = "Other"

            lines.append(f"\n### {title}")
            for commit in commit_groups[commit_type]:
                lines.append(f"* {commit.format()}")

    return "\n".join(lines).strip()
