import pytest
from conftest import (
    BREAKING_FEATURE_IN_BODY,
    CHORE,
    FEATURE,
    FIX,
    INITIAL_COMMIT,
    GitFactory,
)

from convbump.__main__ import _run
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

