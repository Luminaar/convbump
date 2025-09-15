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
    SQUASHED_MERGE_MIXED_PRIORITIES,
    SQUASHED_MERGE_NO_CONVENTIONAL,
    SQUASHED_MERGE_ONLY_FIXES,
    SQUASHED_MERGE_WITH_BREAKING,
    SQUASHED_MERGE_WITH_BREAKING_PRIORITY,
    SQUASHED_MERGE_WITH_FEAT,
    SQUASHED_MERGE_WITH_FIX,
    GitFactory,
)

from convbump.conventional import (
    CommitType,
    ConventionalCommit,
    find_conventional_commit_in_body,
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
    # Non-conventional commits should be treated as OTHER type, not raise ValueError
    conventional = create_conventional_commit(INITIAL_COMMIT)
    assert conventional.commit_type == CommitType.OTHER
    assert conventional.subject == INITIAL_COMMIT


def make_commit(commit_message: str) -> Commit:
    subject, *rest = commit_message.split("\n")
    body = "\n".join(rest) if rest else None

    return Commit(b"f392ca5", subject, body)


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


def test_squashed_merge_with_mixed_types() -> None:
    """Test parsing a squashed merge with mixed commit types - should select highest priority."""
    git_commit = make_commit(SQUASHED_MERGE_WITH_FIX)
    conventional = ConventionalCommit.from_git_commit(git_commit)

    # Should find feat (highest priority) over fix commits in the body
    assert conventional.commit_type == CommitType.FEAT
    assert conventional.scope is None
    assert conventional.is_breaking is False
    assert conventional.subject == "supporting emojis"
    assert conventional.raw_subject == "Refactoring and cleanup (#42)"


def test_squashed_merge_with_feat() -> None:
    """Test parsing a squashed merge that contains feat commits in the body."""
    git_commit = make_commit(SQUASHED_MERGE_WITH_FEAT)
    conventional = ConventionalCommit.from_git_commit(git_commit)

    # Should find the feat commit in the body
    assert conventional.commit_type == CommitType.FEAT
    assert conventional.scope is None
    assert conventional.is_breaking is False
    assert conventional.subject == "add quantum flux capacitor"
    assert conventional.raw_subject == "Feature implementation (#15)"


def test_squashed_merge_with_breaking() -> None:
    """Test parsing a squashed merge that contains breaking changes in the body."""
    git_commit = make_commit(SQUASHED_MERGE_WITH_BREAKING)
    conventional = ConventionalCommit.from_git_commit(git_commit)

    # Should find the breaking feat commit in the body
    assert conventional.commit_type == CommitType.FEAT
    assert conventional.scope is None
    assert conventional.is_breaking is True
    assert conventional.subject == "rewrite neural network core"
    assert conventional.raw_subject == "Major refactor (#99)"


def test_squashed_merge_no_conventional() -> None:
    """Test parsing a squashed merge that contains no conventional commits."""
    git_commit = make_commit(SQUASHED_MERGE_NO_CONVENTIONAL)
    conventional = ConventionalCommit.from_git_commit(git_commit)

    # Should treat as OTHER since no conventional commits found
    assert conventional.commit_type == CommitType.OTHER
    assert conventional.scope is None
    assert conventional.is_breaking is False
    assert conventional.subject == "General improvements (#42)"
    assert conventional.raw_subject == "General improvements (#42)"


def test_find_conventional_commit_in_body() -> None:
    """Test the helper function for finding conventional commits in body text."""
    body = """* Some changes
* More changes
* fix: important bug fix
* Additional changes"""

    result = find_conventional_commit_in_body(body)
    assert result is not None
    commit_type, scope, is_breaking, subject = result
    assert commit_type == "fix"
    assert scope is None
    assert is_breaking is False
    assert subject == "important bug fix"

    # Test with no conventional commits in body
    body_no_conv = """* Some changes
* More changes  
* Additional changes"""

    result = find_conventional_commit_in_body(body_no_conv)
    assert result is None

    # Test with empty body
    assert find_conventional_commit_in_body("") is None
    # Note: find_conventional_commit_in_body expects a string, not None
    # In practice, we check for None before calling this function


def test_priority_based_selection_mixed() -> None:
    """Test that feat (minor bump) is selected over fix/chore/docs (patch bump)."""
    git_commit = make_commit(SQUASHED_MERGE_MIXED_PRIORITIES)
    conventional = ConventionalCommit.from_git_commit(git_commit)

    # Should find feat (priority 2, minor bump) over fix/chore/docs (priority 1, patch bump)
    assert conventional.commit_type == CommitType.FEAT
    assert conventional.scope is None
    assert conventional.is_breaking is False
    assert conventional.subject == "add new API endpoint"
    assert conventional.raw_subject == "Mixed changes (#123)"


def test_priority_based_selection_breaking_wins() -> None:
    """Test that feat! (breaking, major bump) has highest priority."""
    git_commit = make_commit(SQUASHED_MERGE_WITH_BREAKING_PRIORITY)
    conventional = ConventionalCommit.from_git_commit(git_commit)

    # Should find feat! (priority 3, major bump) over feat (priority 2, minor bump), etc.
    assert conventional.commit_type == CommitType.FEAT
    assert conventional.scope is None
    assert conventional.is_breaking is True
    assert conventional.subject == "complete API redesign"
    assert conventional.raw_subject == "Major update (#456)"


def test_priority_based_selection_only_fixes() -> None:
    """Test that when only fix and perf are present, both have same priority so first one is selected."""
    git_commit = make_commit(SQUASHED_MERGE_ONLY_FIXES)
    conventional = ConventionalCommit.from_git_commit(git_commit)

    # Should find first commit since fix and perf both have priority 1 (patch version bump)
    assert conventional.commit_type == CommitType.FIX
    assert conventional.scope is None
    assert conventional.is_breaking is False
    assert conventional.subject == "connection timeout"  # First commit in the list
    assert conventional.raw_subject == "Bug fixes (#789)"


def test_version_impact_priority() -> None:
    """Test the version impact priority calculation function directly."""
    from convbump.conventional import VersionImpact, get_commit_version_impact

    # Test semantic versioning priorities
    # Breaking changes = major version bump
    assert get_commit_version_impact("feat", True) == VersionImpact.MAJOR
    assert get_commit_version_impact("fix", True) == VersionImpact.MAJOR
    assert get_commit_version_impact("chore", True) == VersionImpact.MAJOR
    assert get_commit_version_impact("unknown", True) == VersionImpact.MAJOR

    # feat = minor version bump
    assert get_commit_version_impact("feat", False) == VersionImpact.MINOR

    # Everything else = patch version bump
    assert get_commit_version_impact("fix", False) == VersionImpact.PATCH
    assert get_commit_version_impact("perf", False) == VersionImpact.PATCH
    assert get_commit_version_impact("refactor", False) == VersionImpact.PATCH
    assert get_commit_version_impact("chore", False) == VersionImpact.PATCH
    assert get_commit_version_impact("docs", False) == VersionImpact.PATCH
    assert get_commit_version_impact("unknown", False) == VersionImpact.PATCH


def test_priority_selection_preserves_scope() -> None:
    """Test that scope is preserved in priority-based selection."""
    body = """Multiple changes
* fix(api): connection timeout
* feat(ui): add dark mode
* chore: update deps"""

    result = find_conventional_commit_in_body(body)
    assert result is not None
    commit_type, scope, is_breaking, subject = result

    # Should select feat over fix
    assert commit_type == "feat"
    assert scope == "ui"
    assert is_breaking is False
    assert subject == "add dark mode"


@pytest.mark.skip()
def test_conventional_changelog() -> None:
    """Unskip this function to generate a local markdown file with the changelog."""
    commits = map(ConventionalCommit.from_git_commit, map(make_commit, FORMAT_PARAMS))

    with open("output.md", "w") as f:
        f.write(format_changelog(list(commits)))
