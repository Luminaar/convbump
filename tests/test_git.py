import pytest
from conftest import BREAKING_FEATURE, INITIAL_COMMIT, GitFactory
from semver import VersionInfo as Version

from convbump.git import TAG_REGEX


def test_repository_empty(create_git_repository: GitFactory) -> None:
    git = create_git_repository([])

    assert len(git.list_commits(None)) == 0


def test_repository_list_commits_from_ref(create_git_repository: GitFactory) -> None:

    commits = ["First", ("Second", "v1"), "Third", "Fourth"]
    git = create_git_repository(commits)

    commit_list = git.list_commits("v1")

    assert len(commit_list) == 2

    assert [c.subject for c in commit_list] == ["Third", "Fourth"]


def test_repository_list_commits_from_ref_to_ref(create_git_repository: GitFactory) -> None:

    commits = [("First", "v1"), "Second", "Third", ("Fourth", "v2"), "Fifth"]
    git = create_git_repository(commits)

    commit_list = git.list_commits("v1", "v2")

    assert len(commit_list) == 3

    assert [c.subject for c in commit_list] == ["Second", "Third", "Fourth"]


PARAMS = [
    ("v1", Version(1, 0, 0)),
    ("v10", Version(10, 0, 0)),
    ("v1.0", Version(1, 0, 0)),
    ("v1.1.10", Version(1, 1, 10)),
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
