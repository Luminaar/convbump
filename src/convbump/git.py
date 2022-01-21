import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Tuple

from semver import VersionInfo as Version

# Default version tag regex. It is used to find the last valid git tag.
# This regex will match the following tags: "v1", "v1.0", "v1.0.0"
TAG_REGEX = re.compile(
    r"""^
        v                           # literal 'v'
        (?P<major>\d+)              # Major version is required
        (?:\.                       # Optional non-capturing group with minor and patch versions
            (?P<minor>\d+)          # Optional minor version
            (?:\.                   # Optional non-capturing group with just the patch version
                (?P<patch>\d+)      # Optional patch version
            )?
        )?
        $
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class Commit:

    hash: str
    subject: str
    body: Optional[str]


class Git:
    def __init__(self, path: Path) -> None:
        self.path = path

    def list_commits(self, from_ref: Optional[str], to_ref: Optional[str] = None) -> List[Commit]:
        def iter_commtis(commit_ids: Iterable[str]) -> Iterator[Commit]:
            for commit_id in commit_ids:
                yield self._parse_commits(["git", "log", "-1", r"--format=%h%n%s%n%b", commit_id])

        if from_ref is None:
            command = ["git", "log", "--format=%H"]
        elif from_ref and to_ref:
            command = ["git", "log", "--format=%H", f"{from_ref}..{to_ref}"]
        else:
            command = ["git", "log", "--format=%H", f"{from_ref}..HEAD"]

        try:
            commit_ids = reversed(self._check_output(command).splitlines())
        except subprocess.CalledProcessError:
            return []

        return [commit for commit in iter_commtis(commit_ids)]

    def retrieve_last_commit(self) -> str:
        return self._check_output(["git", "log", "-1", "--format=%B"])

    def retrieve_last_version(self) -> Tuple[Optional[str], Optional[Version]]:
        """Retrieve last valid version from a tag. Any non-valid version tags are skipped.
        Return a tuple with tag name and version or None."""

        tags = reversed(self._check_output(["git", "tag", "--sort=v:refname"]).split("\n"))
        for tag in tags:
            match = TAG_REGEX.match(tag)
            if match:
                match_dict = match.groupdict()
                return tag, Version(
                    match_dict["major"], match_dict["minor"] or 0, match_dict["patch"] or 0
                )
        else:
            return None, None

    def retrieve_tag_body(self, tag: str) -> str:
        return self._check_output(["git", "tag", "-l", "--format=%(body)", tag])

    def retrieve_tag_subject(self, tag: str) -> str:
        return self._check_output(["git", "tag", "-l", "--format=%(subject)", tag])

    def _check_output(self, args: List[str]) -> str:
        maybe_output = subprocess.check_output(args, cwd=self.path)
        if maybe_output is not None:
            return maybe_output.strip().decode("utf-8")

        raise ValueError("git command return unexpected empty output")

    def _parse_commits(self, args: List[str]) -> Commit:
        maybe_output = subprocess.check_output(args, cwd=self.path)
        if maybe_output is not None:
            output = maybe_output.strip().decode("utf-8")

            hash, subject, *body = output.split("\n")

            return Commit(hash, subject, "\n".join(body) if body else None)

        raise ValueError("git command return unexpected empty output")
