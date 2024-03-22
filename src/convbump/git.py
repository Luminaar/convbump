import re
from dataclasses import dataclass, field
from operator import itemgetter
from pathlib import Path
from typing import List, Optional, Set, Tuple

from dulwich.objects import Commit as RawCommit
from dulwich.repo import Repo
from semver import VersionInfo as Version

# Default version tag regex. It is used to find the last valid git tag.
# This regex will match the following tags: "v1", "v1.0", "v1.0.0"
TAG_REGEX = re.compile(
    r"""^
        refs/tags/                  # literal 'refs/tags/
        (?:                         # Optional non-campturing group with the scope
            (?P<scope>.*)           # Optional scope
            /                       # Literal '/' (delimiter)
        )?
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

    hash: bytes
    subject: str
    body: Optional[str]
    paths: Set[Path] = field(default_factory=set)

    def affects_dir(self, dir: str) -> bool:
        for path in self.paths:
            try:
                if path.relative_to(dir):
                    return True
            except ValueError:
                pass
        else:
            return False


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

    def get_commit_paths(self, commit: RawCommit) -> Set[Path]:
        parents = [self.repo[parent] for parent in commit.parents]
        paths: Set[Path] = set()
        for parent_commit in parents:
            old_tree = parent_commit.tree
            new_tree = commit.tree
            for (old_path, new_path), _, _ in self.repo.object_store.tree_changes(old_tree, new_tree):  # type: ignore
                if old_path:
                    paths.add(Path(old_path.decode()))
                if new_path:
                    paths.add(Path(new_path.decode()))
        return paths

    def list_commits(
        self, from_tag: Optional[bytes], to_tag: Optional[bytes] = None
    ) -> List[Commit]:
        """List commits from `from_tag` to `to_tag`. If `to_tag` is None,
        list commits until the latest commits.

        If `from_tag` list commits from the first commits.

        If `from_tag` and `to_tag` is None, list all commits.

        `from_tag` and `to_tag` must be a full tag name:

            refs/tags/tag_name
        """

        try:
            walker = self.repo.get_walker(reverse=True)
        except KeyError:  # Repo is empty
            return []

        # Convert from_ref to SHA if it is a tag name
        from_sha = self.repo.get_peeled(from_tag) if from_tag else None

        # Convert to_ref to SHA if it is a tag name
        to_sha = self.repo.get_peeled(to_tag) if to_tag else None

        if from_sha is None:
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
                paths = self.get_commit_paths(commit)
                commits.append(Commit(hash, subject, body or None, paths))

            if hash == from_sha:
                add = True
            if to_tag and hash == to_sha:
                break

        return commits

    def retrieve_last_version(
        self, scope: Optional[str] = None
    ) -> Tuple[Optional[bytes], Optional[Version]]:
        """Retrieve last valid version from a tag. Any non-valid version tags are skipped.
        Return a tuple with tag name and version or None.

        If `scope` is not None, only consider tags with this scope."""

        tag_refs = filter(lambda ref: ref.startswith(b"refs/tags"), self.repo.get_refs())

        tag_version_list = []
        for tag in tag_refs:
            match = TAG_REGEX.match(tag.decode())
            if match:
                match_dict = match.groupdict()

                matched_scope = match_dict.get("scope")

                if scope == matched_scope:
                    tag_version_list.append(
                        (
                            tag,
                            Version(
                                match_dict["major"],  # type: ignore
                                match_dict["minor"] or 0,  # type: ignore
                                match_dict["patch"] or 0,  # type: ignore
                            ),
                        )
                    )

        sorted_tags = sorted(tag_version_list, key=itemgetter(1))

        if sorted_tags:
            return sorted_tags[-1]
        else:
            return None, None
