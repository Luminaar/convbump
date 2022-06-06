from pathlib import Path
from typing import Tuple

import pytest
from conftest import BREAKING_FEATURE, INITIAL_COMMIT, GitFactory
from semver import VersionInfo as Version

from convbump.git import TAG_REGEX, Commit, parse_message

def test_affects_dir() -> None:
    commit = Commit(b"hash", "subject", "message", {Path("lib_a/src/lib_a/module.py"), Path("lib_a/src/lib_a/util.py")})

    assert commit.affects_dir("lib_a")
    assert commit.affects_dir("lib_a/src")
    assert not commit.affects_dir("lib_b")
    assert not commit.affects_dir("lib_b/src")

MESSAGES = [
    ("Subject\n\nBody", ("Subject", "Body")),
    ("Subject\n\nParagraph\n\nParagraph", ("Subject", "Paragraph\n\nParagraph")),
    ("Subject", ("Subject", "")),
    ("First line\nSecond line", ("", "First line\nSecond line")),
    ("", ("", "")),
]


@pytest.mark.parametrize("message, result", MESSAGES)
def test_parse_message(message: str, result: Tuple[str, str]) -> None:

    assert parse_message(message) == result


def test_repository_empty(create_git_repository: GitFactory) -> None:
    git = create_git_repository([])

    assert len(git.list_commits(None)) == 0


def test_repository_list_commits(create_git_repository: GitFactory) -> None:
    commits = ["First", "Second"]
    git = create_git_repository(commits)

    commit_list = git.list_commits(None)

    assert len(commit_list) == 2

    assert [c.subject for c in commit_list] == ["First", "Second"]


def test_repository_list_commits_from_ref(create_git_repository: GitFactory) -> None:

    commits = ["First", ("Second", "v1"), "Third", "Fourth"]
    git = create_git_repository(commits)

    commit_list = git.list_commits(b"refs/tags/v1")

    assert len(commit_list) == 2

    assert [c.subject for c in commit_list] == ["Third", "Fourth"]


def test_repository_list_commits_from_ref_to_ref(create_git_repository: GitFactory) -> None:

    commits = [("First", "v1"), "Second", "Third", ("Fourth", "v2"), "Fifth"]
    git = create_git_repository(commits)

    commit_list = git.list_commits(b"refs/tags/v1", b"refs/tags/v2")

    assert len(commit_list) == 3

    assert [c.subject for c in commit_list] == ["Second", "Third", "Fourth"]


def test_repository_list_commits_to_ref(create_git_repository: GitFactory) -> None:

    commits = [("First", "v1"), "Second", "Third", ("Fourth", "v2"), "Fifth"]
    git = create_git_repository(commits)

    commit_list = git.list_commits(None, b"refs/tags/v2")

    assert len(commit_list) == 4

    assert [c.subject for c in commit_list] == ["First", "Second", "Third", "Fourth"]


PARAMS = [
    ("refs/tags/v1", Version(1, 0, 0)),
    ("refs/tags/v10", Version(10, 0, 0)),
    ("refs/tags/v1.0", Version(1, 0, 0)),
    ("refs/tags/v1.1.10", Version(1, 1, 10)),
]


@pytest.mark.parametrize("tag, version", PARAMS)
def test_git_tag_regex(tag: str, version: Version) -> None:
    match = TAG_REGEX.match(tag)
    assert match is not None
    match_dict = match.groupdict()

    major = match_dict["major"]
    minor = match_dict["minor"] or 0
    patch = match_dict["patch"] or 0

    assert Version(major, minor, patch) == version


def test_repository_get_last_valid_version_tag(create_git_repository: GitFactory) -> None:
    commits = [(INITIAL_COMMIT, "initial"), ("First", "v1.0.0"), ("Second", "not-a-version")]
    git = create_git_repository(commits)

    _, version = git.retrieve_last_version()
    assert version == Version(1, 0, 0)


def test_repository_get_last_valid_version_tag_from_multiple(
    create_git_repository: GitFactory,
) -> None:
    commits = [("First", "v1.0.0"), (BREAKING_FEATURE, "v2.0.0")]
    git = create_git_repository(commits)

    _, version = git.retrieve_last_version()
    assert version == Version(2, 0, 0)


def test_repository_no_tags(create_git_repository: GitFactory) -> None:
    git = create_git_repository([INITIAL_COMMIT])

    assert git.retrieve_last_version() == (None, None)


def test_repository_not_valid_tags(create_git_repository: GitFactory) -> None:
    git = create_git_repository([(INITIAL_COMMIT, "not-a-version"), ("Second", "not-a-version-2")])

    assert git.retrieve_last_version() == (None, None)


def test_tag_order(create_git_repository: GitFactory) -> None:
    git = create_git_repository(
        [(INITIAL_COMMIT, "v1"), ("Second", "v1.9.0"), ("Third", "v1.10.0")]
    )

    _, version = git.retrieve_last_version()
    assert version == Version(1, 10, 0)


def test_get_tag_with_directory(create_git_repository: GitFactory) -> None:
    directory = "core"
    git = create_git_repository(
        [(INITIAL_COMMIT, "core/v1"), ("Second", "core/v1.1.0"), ("Unrelated", "api/v0.1.0")]
    )

    tag_name, version = git.retrieve_last_version(directory)
    assert tag_name == b"refs/tags/core/v1.1.0"
    assert version == Version(1, 1, 0)

def test_get_tag_with_directory_nested(create_git_repository: GitFactory) -> None:
    directory = "core/consumer"
    git = create_git_repository(
        [(INITIAL_COMMIT, "core/consumer/v1"), ("Second", "core/consumer/v1.1.0"), ("Unrelated", "api/v0.1.0")]
    )

    tag_name, version = git.retrieve_last_version(directory)
    assert tag_name == b"refs/tags/core/consumer/v1.1.0"
    assert version == Version(1, 1, 0)

def test_get_tag_with_directory_no_match(create_git_repository: GitFactory) -> None:
    directory = "core"
    git = create_git_repository(
        [(INITIAL_COMMIT, "api/v1"), ("Second", "api/v1.1.0")]
    )

    assert git.retrieve_last_version(directory) == (None, None)