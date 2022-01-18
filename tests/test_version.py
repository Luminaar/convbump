from typing import List
import pytest

from convbump.conventional import CommitType
from convbump.conventional import ConventionalCommit as CC
from convbump.version import DEFAULT_FIRST_VERSION, get_next_version

def test_get_next_version_do_nothing() -> None:
    next_version = get_next_version(DEFAULT_FIRST_VERSION, [])
    assert next_version == DEFAULT_FIRST_VERSION


BREAKING_PARAMS = [
    [CC(CommitType.FEAT, None, True, "", "", "")],  # Single breaking feature
    [
        CC(CommitType.FEAT, None, True, "", "", ""),
        CC(CommitType.FIX, None, False, "", "", ""),
    ],  # Breaking feature and a fix
    [
        CC(CommitType.FEAT, None, True, "", "", ""),
        CC(CommitType.FIX, None, True, "", "", ""),
    ],  # Two breaking changes
    [
        CC(CommitType.FEAT, None, False, "", "", ""),
        CC(CommitType.FIX, None, True, "", "", ""),
    ],  # Breaking fix
    [CC(CommitType.FIX, None, True, "", "", "")],  # Single breaking fix
    [CC(CommitType.OTHER, None, True, "", "", "")],  # Breaking other
]


@pytest.mark.parametrize("commits", BREAKING_PARAMS)
def test_get_next_version_bump_major(commits: List[CC]) -> None:

    next_version = get_next_version(DEFAULT_FIRST_VERSION, commits)

    assert next_version.major == DEFAULT_FIRST_VERSION.major + 1
    assert next_version.minor == 0
    assert next_version.patch == 0


MINOR_PARAMS = [
    [CC(CommitType.FEAT, None, False, "", "", "")],  # Single non-breaking feature
    [
        CC(CommitType.FEAT, None, False, "", "", ""),
        CC(CommitType.FEAT, None, False, "", "", ""),
    ],  # Two non-breaking features
    [
        CC(CommitType.FEAT, None, False, "", "", ""),
        CC(CommitType.FIX, None, False, "", "", ""),
    ],  # Feature and a fix
]


@pytest.mark.parametrize("commits", MINOR_PARAMS)
def test_get_next_version_bump_minor(commits: List[CC]) -> None:

    next_version = get_next_version(DEFAULT_FIRST_VERSION, commits)

    assert next_version.major == DEFAULT_FIRST_VERSION.major
    assert next_version.minor == DEFAULT_FIRST_VERSION.minor + 1
    assert next_version.patch == 0


PATCH_PARAMS = [
    [CC(CommitType.FIX, None, False, "", "", "")],  # Single non-breaking fix
    [
        CC(CommitType.FIX, None, False, "", "", ""),
        CC(CommitType.FIX, None, False, "", "", ""),
    ],  # Two non-breaking fixes
    [CC(CommitType.CHORE, None, False, "", "", "")],
    [CC(CommitType.DOCS, None, False, "", "", "")],
    [CC(CommitType.TEST, None, False, "", "", "")],
    [CC(CommitType.REFACTOR, None, False, "", "", "")],
    [CC(CommitType.STYLE, None, False, "", "", "")],
    [CC(CommitType.CI, None, False, "", "", "")],
    [CC(CommitType.OTHER, None, False, "", "", "")],
]


@pytest.mark.parametrize("commits", PATCH_PARAMS)
def test_get_next_version_bump_patch(commits: List[CC]) -> None:

    next_version = get_next_version(DEFAULT_FIRST_VERSION, commits)

    assert next_version.major == DEFAULT_FIRST_VERSION.major
    assert next_version.minor == DEFAULT_FIRST_VERSION.minor
    assert next_version.patch == DEFAULT_FIRST_VERSION.patch + 1
