from typing import List

import pytest
from conftest import (
    BREAKING_FEATURE_IN_BODY,
    CHORE,
    FEATURE,
    FIX,
    INITIAL_COMMIT,
    GitFactory,
)

from convbump.__main__ import _run, ignore_commit
from convbump.conventional import CommitType, ConventionalCommit
from convbump.version import DEFAULT_FIRST_VERSION


def test_new_repo(create_git_repository: GitFactory) -> None:
    git = create_git_repository([INITIAL_COMMIT])
    next_version, _ = _run(git, False)
    assert next_version == DEFAULT_FIRST_VERSION


def test_not_version_tag(create_git_repository: GitFactory) -> None:
    git = create_git_repository([(INITIAL_COMMIT, "not-a-version"), FEATURE])
    next_version, _ = _run(git, False)
    assert next_version == DEFAULT_FIRST_VERSION


def test_no_new_commits_after_tag(create_git_repository: GitFactory) -> None:
    git = create_git_repository([(INITIAL_COMMIT, "v1.0.0")])
    with pytest.raises(ValueError):
        _run(git, False)


def test_no_conventional_commit_after_tag_strict(create_git_repository: GitFactory) -> None:
    git = create_git_repository([(INITIAL_COMMIT, "v1.0.0"), "Non-conventional commit"])
    with pytest.raises(ValueError):
        _run(git, True)


def test_no_conventional_commit_after_tag_not_strict(create_git_repository: GitFactory) -> None:
    git = create_git_repository([(INITIAL_COMMIT, "v1.0.0"), "Non-conventional commit"])
    with pytest.raises(ValueError):
        _run(git, False)


def test_find_last_valid_version_tag(create_git_repository: GitFactory) -> None:
    git = create_git_repository(
        [(INITIAL_COMMIT, "v0.1.0"), ("Second commit", "not-a-version"), BREAKING_FEATURE_IN_BODY]
    )
    next_version, _ = _run(git, False)
    assert next_version == DEFAULT_FIRST_VERSION.bump_major()


def test_non_conventional_commits_strict(create_git_repository: GitFactory) -> None:
    git = create_git_repository([(INITIAL_COMMIT, "v0.1.0"), FEATURE, "Non-conventional commit"])
    with pytest.raises(ValueError):
        _run(git, True)


def test_non_conventional_commits_not_strict(create_git_repository: GitFactory) -> None:
    git = create_git_repository([(INITIAL_COMMIT, "v0.1.0"), FEATURE, "Non-conventional commit"])
    next_version, _ = _run(git, False)
    assert next_version == DEFAULT_FIRST_VERSION.bump_minor()


def test_conventional_commits(create_git_repository: GitFactory) -> None:
    git = create_git_repository([(INITIAL_COMMIT, "v0.1.0"), FEATURE, FIX])
    next_version, _ = _run(git, False)
    assert next_version == DEFAULT_FIRST_VERSION.bump_minor()


@pytest.mark.parametrize(
    "patterns, commit, result",
    [
        (
            ["aiohttp"],
            ConventionalCommit(
                CommitType.CHORE,
                "deps",
                False,
                "Update aiohttp",
                "",
                "",
                "chore(deps): Update aiohttp",
            ),
            True,
        ),
        (
            ["aiohttp"],
            ConventionalCommit(
                CommitType.CHORE,
                "deps",
                False,
                "Update deps",
                "Update aiohttp",
                "",
                "chore(deps): Update aiohttp",
            ),
            True,
        ),
        (
            ["deps"],
            ConventionalCommit(
                CommitType.CHORE,
                "deps",
                False,
                "Update aiohttp",
                "",
                "",
                "chore(deps): Update aiohttp",
            ),
            True,
        ),
        (
            ["chore"],
            ConventionalCommit(
                CommitType.CHORE,
                "deps",
                False,
                "Update aiohttp",
                "",
                "",
                "chore(deps): Update aiohttp",
            ),
            True,
        ),
        (
            ["feat", "aiohttp"],
            ConventionalCommit(
                CommitType.CHORE,
                "deps",
                False,
                "Update aiohttp",
                "",
                "",
                "chore(deps): Update aiohttp",
            ),
            True,
        ),
        (
            [""],
            ConventionalCommit(
                CommitType.CHORE,
                "deps",
                False,
                "Update aiohttp",
                "",
                "",
                "chore(deps): Update aiohttp",
            ),
            False,
        ),
        (
            ["formatting"],
            ConventionalCommit(
                CommitType.CHORE,
                "deps",
                False,
                "Update aiohttp",
                "",
                "",
                "chore(deps): Update aiohttp",
            ),
            False,
        ),
    ],
)
def test_ignore_commit(patterns: List[str], commit: ConventionalCommit, result: bool) -> None:
    assert ignore_commit(patterns, commit) is result


def test_ignore_prefix(create_git_repository: GitFactory) -> None:
    git = create_git_repository([(INITIAL_COMMIT, "v0.1.0"), CHORE])

    with pytest.raises(
        ValueError
    ):  # The chore commit should be skipped, so there are no new commits left
        _run(git, False, ignored_patterns=["chore"])
