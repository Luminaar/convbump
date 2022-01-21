from typing import Callable, Optional, Tuple

import pytest
from conftest import (
    BREAKING_FEATURE,
    BREAKING_FEATURE_IN_BODY,
    BREAKING_FEATURE_WITH_SCOPE,
    BREAKING_FIX,
    BREAKING_FIX_IN_BODY,
    BREAKING_FIX_WITH_SCOPE,
    CHORE,
    CHORE_WITH_SCOPE,
    FEATURE,
    FEATURE_CASED,
    FEATURE_WITH_SCOPE,
    FIX,
    FIX_CASED,
    FIX_WITH_SCOPE,
    INITIAL_COMMIT,
    OTHER_COMMIT,
    GitFactory,
)

from convbump.conventional import (
    CommitType,
    ConventionalCommit,
    format_changelog,
    parse_subject,
)
from convbump.git import Commit

ConventionalFactory = Callable[[str], ConventionalCommit]

REGEX_PARAMS = [
    (
        "feat: feature",
        ("feat", None, False, "feature"),
    ),
    ("fix(core): new fix", ("fix", "core", False, "new fix")),
    ("feat!: breaking feature", ("feat", None, True, "breaking feature")),
    ("feat(core-app)!: breaking", ("feat", "core-app", True, "breaking")),
]


@pytest.mark.parametrize("subject, result", REGEX_PARAMS)
def test_subject_regex(subject: str, result: Tuple[str, str, bool, str]) -> None:
    assert parse_subject(subject) == result


@pytest.mark.parametrize(
    "subject",
    [
        "feat",
        "feat:",
    ],
)
def test_subject_regex_invalid(subject: str) -> None:
    with pytest.raises(ValueError):
        parse_subject(subject)


@pytest.fixture()
def create_conventional_commit(create_git_repository: GitFactory) -> ConventionalFactory:
    def _(message: str) -> ConventionalCommit:
        git = create_git_repository([(message, None)])
        commit = git.list_commits(None)[0]
        return ConventionalCommit.from_git_commit(commit)

    return _


def test_conventinal_invalid(create_conventional_commit: ConventionalFactory) -> None:
    with pytest.raises(ValueError):
        create_conventional_commit(INITIAL_COMMIT)


def make_commit(commit_message: str) -> Commit:
    subject, *rest = commit_message.split("\n")
    body = "\n".join(rest) if rest else None

    return Commit("f392ca5", subject, body)


COMMIT_PARAMS = [
    (FEATURE, CommitType.FEAT, None, False),
    (FEATURE_CASED, CommitType.FEAT, None, False),
    (FEATURE_WITH_SCOPE, CommitType.FEAT, "core", False),
    (BREAKING_FEATURE, CommitType.FEAT, None, True),
    (BREAKING_FEATURE_WITH_SCOPE, CommitType.FEAT, "core", True),
    (BREAKING_FEATURE_IN_BODY, CommitType.FEAT, None, True),
    (FIX, CommitType.FIX, None, False),
    (FIX_CASED, CommitType.FIX, None, False),
    (FIX_WITH_SCOPE, CommitType.FIX, "core", False),
    (BREAKING_FIX, CommitType.FIX, None, True),
    (BREAKING_FIX_WITH_SCOPE, CommitType.FIX, "core", True),
    (BREAKING_FIX_IN_BODY, CommitType.FIX, None, True),
    (CHORE, CommitType.CHORE, None, False),
    (CHORE_WITH_SCOPE, CommitType.CHORE, "deps", False),
    (OTHER_COMMIT, CommitType.OTHER, None, False),
]


@pytest.mark.parametrize("message, commit_type, scope, is_breaking", COMMIT_PARAMS)
def test_conventional_commit(
    message: str, commit_type: CommitType, scope: Optional[str], is_breaking: bool
) -> None:
    git_commit = make_commit(message)
    conventional = ConventionalCommit.from_git_commit(git_commit)

    print(message, "|", conventional.subject)
    assert conventional.commit_type == commit_type
    assert conventional.scope == scope
    assert conventional.is_breaking == is_breaking


FORMAT_PARAMS = [
    FEATURE,
    FEATURE_CASED,
    FEATURE_WITH_SCOPE,
    BREAKING_FEATURE,
    BREAKING_FEATURE_WITH_SCOPE,
    BREAKING_FEATURE_IN_BODY,
    FIX,
    FIX_CASED,
    FIX_WITH_SCOPE,
    BREAKING_FIX,
    BREAKING_FIX_WITH_SCOPE,
    BREAKING_FIX_IN_BODY,
    CHORE,
    CHORE_WITH_SCOPE,
    OTHER_COMMIT,
]


@pytest.mark.parametrize(
    "message",
    FORMAT_PARAMS,
)
def test_conventional_format(message: str) -> None:
    git_commit = make_commit(message)
    conventional = ConventionalCommit.from_git_commit(git_commit)
    print()
    print(conventional.format())


@pytest.mark.skip()
def test_conventional_changelog() -> None:
    """Unskip this function to generate a local markdown file with the changelog."""
    commits = map(ConventionalCommit.from_git_commit, map(make_commit, FORMAT_PARAMS))

    with open("output.md", "w") as f:
        f.write(format_changelog(list(commits)))
