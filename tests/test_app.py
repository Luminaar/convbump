import pytest

from cocobump.app import run
from cocobump.configs import ProjectConfig

INITIAL_COMMIT = ("initial.txt", "initial commit", "Initial commit")
FEATURE_COMMIT = ("feature.txt", "feature", "feat: first feature")
BREAKING_COMMIT = ("breaking.txt", "breaking feature", "feat!: breaking change")
FIX_COMMIT = ("fix.txt", "fix", "fix: first fix")
NON_CONVENTIONAL_COMMIT = ("fix.txt", "non-conventional fix", "non conventional commit")

INITIAL_TAG = ("v1.0.0", "Initial release")


@pytest.fixture
def project_config():
    return ProjectConfig()


@pytest.fixture
def initial_repository(create_git_repository):

    return create_git_repository(INITIAL_COMMIT, tag=INITIAL_TAG)


def test_empty_repository(create_git_repository, project_config):
    """If the repository is empty, return no changelog and the initial version."""

    git = create_git_repository()

    next_version, changelog = run(project_config, git, False)
    assert next_version.format(config=project_config) == "1.0.0"
    assert len(changelog.commits) == 0


def test_commits_with_no_tag(create_git_repository, project_config):
    """If the repository is not empty but there is no tag, return initial
    version and a changelog with all conventional commits."""

    git = create_git_repository(FEATURE_COMMIT, FIX_COMMIT, NON_CONVENTIONAL_COMMIT)

    next_version, changelog = run(project_config, git, False)
    assert next_version.format(config=project_config) == "1.0.0"
    assert len(changelog.commits) == 2


def test_no_commits_after_tag(initial_repository, project_config):
    """If there is a tag but no commits after it, fail."""

    with pytest.raises(ValueError):
        run(project_config, initial_repository, False)


def test_no_conventional_commits_after_tag(initial_repository, create_git_commit, project_config):
    """If there is a tag but no conventional commits after it, fail."""

    create_git_commit(initial_repository.path, NON_CONVENTIONAL_COMMIT)

    with pytest.raises(ValueError):
        run(project_config, initial_repository, False)


def test_feature_commit(initial_repository, create_git_commit, project_config):
    """If there is one feature commit, bump the minor version."""

    create_git_commit(initial_repository.path, FEATURE_COMMIT)

    next_version, changelog = run(project_config, initial_repository, False)
    assert next_version.format(config=project_config) == "1.1.0"
    assert len(changelog.commits) == 1


def test_mixed_commits(initial_repository, create_git_commit, project_config):
    """If conventional commits are mixed with non-conventional, still bump the
    version but ignore non-conventional commits in the changelog."""

    create_git_commit(initial_repository.path, FEATURE_COMMIT)
    create_git_commit(initial_repository.path, NON_CONVENTIONAL_COMMIT)

    next_version, changelog = run(project_config, initial_repository, False)
    assert next_version.format(config=project_config) == "1.1.0"
    assert len(changelog.commits) == 1


def test_multiple_conventional_commits(initial_repository, create_git_commit, project_config):
    """Only bump version once."""

    create_git_commit(initial_repository.path, FEATURE_COMMIT)
    create_git_commit(initial_repository.path, FIX_COMMIT)

    next_version, changelog = run(project_config, initial_repository, False)
    assert next_version.format(config=project_config) == "1.1.0"
    assert len(changelog.commits) == 2


def test_fix_commit(initial_repository, create_git_commit, project_config):
    """If there is one fix commit, bump the patch version."""

    create_git_commit(initial_repository.path, FIX_COMMIT)

    next_version, changelog = run(project_config, initial_repository, False)
    assert next_version.format(config=project_config) == "1.0.1"
    assert len(changelog.commits) == 1


def test_breaking_commit(initial_repository, create_git_commit, project_config):
    """If there is a breaking change, bump major version."""

    create_git_commit(initial_repository.path, BREAKING_COMMIT)

    next_version, changelog = run(project_config, initial_repository, False)
    assert next_version.format(config=project_config) == "2.0.0"
    assert len(changelog.commits) == 1
