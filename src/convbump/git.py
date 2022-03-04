import re
from dataclasses import dataclass
from operator import itemgetter
from pathlib import Path
from typing import List, Optional, Tuple

from dulwich.objects import Commit as RawCommit
from dulwich.repo import Repo
from semver import VersionInfo as Version

# Default version tag regex. It is used to find the last valid git tag.
# This regex will match the following tags: "v1", "v1.0", "v1.0.0"
TAG_REGEX = re.compile(
    r"""^
        refs/tags/v                 # literal 'refs/tags/v'
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


def parse_message(message: str) -> Tuple[str, str]:  # Tuple[subject, message]
    """Parse git message into subject and body."""

    paragraphs = message.strip().split("\n\n")
    maybe_subject = paragraphs[0]
    if "\n" in maybe_subject:
        subject = ""
        body = message
    else:
        subject = maybe_subject
        body = "\n\n".join(paragraphs[1:])

    return subject, body


class Git:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.repo = Repo(self.path)  # type: ignore

    def list_commits(
        self, from_ref: Optional[bytes], to_ref: Optional[bytes] = None
    ) -> List[Commit]:
        try:
            walker = self.repo.get_walker(reverse=True)
        except KeyError:  # Repo is empty
            return []

        # Convert from_ref to SHA if it is a tag name
        _, from_sha_or_none = self.repo.refs.follow(from_ref or b"")
        from_sha = from_sha_or_none if from_sha_or_none else from_ref

        # Convert to_ref to SHA if it is a tag name
        _, to_sha_or_none = self.repo.refs.follow(to_ref or b"")
        to_sha = to_sha_or_none if to_sha_or_none else to_ref

        if from_sha is None and to_sha is None:
            add = True
        else:
            add = False
        commits: List[Commit] = []
        for entry in walker:
            commit: RawCommit = entry.commit
            hash = commit.id

            if add:
                message = commit.message.decode()
                subject, body = parse_message(message)
                commits.append(Commit(hash, subject, body or None))

            if hash == from_sha:
                add = True
            if to_ref and hash == to_sha:
                break

        return commits

    def retrieve_last_version(self) -> Tuple[Optional[bytes], Optional[Version]]:
        """Retrieve last valid version from a tag. Any non-valid version tags are skipped.
        Return a tuple with tag name and version or None."""

        tag_refs = filter(lambda ref: ref.startswith(b"refs/tags"), self.repo.get_refs())

        tag_version_list = []
        for tag in tag_refs:
            match = TAG_REGEX.match(tag.decode())
            if match:
                match_dict = match.groupdict()

                tag_version_list.append(
                    (
                        tag,
                        Version(
                            match_dict["major"], match_dict["minor"] or 0, match_dict["patch"] or 0
                        ),
                    )
                )

        sorted_tags = sorted(tag_version_list, key=itemgetter(1))

        if sorted_tags:
            return sorted_tags[-1]
        else:
            return None, None
