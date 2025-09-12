from pathlib import Path
from typing import Tuple

import pytest
from conftest import BREAKING_FEATURE, INITIAL_COMMIT, GitFactory
from semver import VersionInfo as Version

from convbump.git import TAG_REGEX, Commit, parse_message


def test_affects_dir() -> None:
    commit = Commit(
        b"hash",
        "subject",
        "message",
        {Path("lib_a/src/lib_a/module.py"), Path("lib_a/src/lib_a/util.py")},
    )

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

    assert Version(major, minor, patch) == version  # type: ignore


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
        [
            (INITIAL_COMMIT, "core/consumer/v1"),
            ("Second", "core/consumer/v1.1.0"),
            ("Unrelated", "api/v0.1.0"),
        ]
    )

    tag_name, version = git.retrieve_last_version(directory)
    assert tag_name == b"refs/tags/core/consumer/v1.1.0"
    assert version == Version(1, 1, 0)


def test_get_tag_with_directory_no_match(create_git_repository: GitFactory) -> None:
    directory = "core"
    git = create_git_repository([(INITIAL_COMMIT, "api/v1"), ("Second", "api/v1.1.0")])

    assert git.retrieve_last_version(directory) == (None, None)


def test_list_commits_includes_chronologically_older_merged_commits(
    create_git_repository: GitFactory,
) -> None:
    """Test that list_commits includes commits that are chronologically older than the from_tag
    but are part of the target branch due to merging. This simulates the GitHub scenario where
    a feature branch with older commits gets merged after a tag is created.

    This test would fail with the old implementation that used chronological filtering.
    """
    import subprocess
    import time

    # Start with just the initial commit
    commits = [INITIAL_COMMIT]
    git = create_git_repository(commits)
    repo_path = git.path

    # Create and checkout feature branch
    subprocess.check_call(["git", "checkout", "-b", "feature-branch"], cwd=repo_path)

    # Add commits to feature branch (these will be chronologically older than the tag)
    feature_commits = [
        "fix(ui): overflow box",
        "wip: migrations versions",
        "chore: refactor columns handling",
        "chore: refactor updates",
        "feat: record transform",
    ]

    for commit_msg in feature_commits:
        subprocess.check_call(["git", "commit", "--allow-empty", "-m", commit_msg], cwd=repo_path)

    # Small delay to ensure chronological separation
    time.sleep(0.1)

    # Go back to master and create the tag AFTER the feature commits
    # This makes the feature commits chronologically older than the tag
    subprocess.check_call(["git", "checkout", "master"], cwd=repo_path)
    subprocess.check_call(
        ["git", "commit", "--allow-empty", "-m", "Prepare release"], cwd=repo_path
    )
    subprocess.check_call(["git", "tag", "-a", "-m", "Release v0.6.2", "v0.6.2"], cwd=repo_path)

    # Small delay to ensure chronological separation
    time.sleep(0.1)

    # Add post-release commits
    subprocess.check_call(
        ["git", "commit", "--allow-empty", "-m", "Post-release fix"], cwd=repo_path
    )

    # Merge the feature branch (this brings in the chronologically older commits)
    subprocess.check_call(
        ["git", "merge", "--no-ff", "-m", "Merge feature branch", "feature-branch"], cwd=repo_path
    )

    # Now test our list_commits function
    commits = git.list_commits(b"refs/tags/v0.6.2", None)

    # We should get all commits from v0.6.2 to HEAD, including the feature branch commits
    commit_subjects = [c.subject for c in commits]

    # Should include the merge commit, post-release fix, and all feature commits
    # The old implementation would miss the feature commits because they're chronologically older
    assert len(commits) >= 7  # At least: merge commit + post-release fix + 5 feature commits
    assert "Merge feature branch" in commit_subjects
    assert "Post-release fix" in commit_subjects
    assert "fix(ui): overflow box" in commit_subjects
    assert "feat: record transform" in commit_subjects

    # Should NOT include the "Prepare release" commit (it's at the tag boundary)
    assert "Prepare release" not in commit_subjects
