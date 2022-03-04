import subprocess
from pathlib import Path
from typing import Callable, Collection, Optional, Tuple, Union

import pytest

from convbump.git import Git

CommitTuple = Tuple[str, str]
GitFactory = Callable[[Collection[CommitTuple]], Git]

INITIAL_COMMIT = "Initial commit"

FEATURE = "feat: A new feature"
FEATURE_CASED = "Feat: A new feature cased"
FEATURE_WITH_SCOPE = "feat(core): A new feature witch scope"
BREAKING_FEATURE = "feat!: Breaking feature"
BREAKING_FEATURE_WITH_SCOPE = "feat(core)!: Breaking feature scoped"
BREAKING_FEATURE_IN_BODY = "feat: Breaking feature in body\n\nBREAKING CHANGE: Breaking feature"

FIX = "fix: A fix"
FIX_CASED = "Fix: A fix"
FIX_WITH_SCOPE = "fix(core): A fix"
BREAKING_FIX = "fix!: Breaking fix"
BREAKING_FIX_WITH_SCOPE = "fix(core)!: Breaking fix"
BREAKING_FIX_IN_BODY = "fix: A fix\n\nBREAKING CHANGE: Breaking fix"

CHORE = "chore: Update deps"
CHORE_WITH_SCOPE = "chore(deps): Update deps"

OTHER_COMMIT = "fake: Some other type of commit"


@pytest.fixture(scope="session")
def git_config() -> None:
    """If user.email and user.name are not set, call git config."""

    try:
        subprocess.check_call(["git", "--no-pager", "config", "--global", "--get-regex", "name"])
        subprocess.check_call(["git", "--no-pager", "config", "--global", "--get-regex", "email"])
    except subprocess.CalledProcessError:
        subprocess.check_call(["git", "config", "--global", "user.email", "'test@test.com'"])
        subprocess.check_call(["git", "config", "--global", "user.name", "'test'"])


@pytest.fixture()
def create_git_repository(
    git_config: None, tmp_path: Path  # pylint: disable=unused-argument
) -> GitFactory:
    def _(commits: Collection[Union[CommitTuple, str]]) -> Git:
        subprocess.check_call(["git", "init"], cwd=tmp_path)

        message: str
        tag: Optional[str]
        for item in commits:
            if isinstance(item, tuple):
                message, tag = item
            else:
                message = item
                tag = None

            subprocess.check_call(["git", "commit", "--allow-empty", "-m", message], cwd=tmp_path)
            if tag is not None:
                subprocess.check_call(["git", "tag", "-a", "-m", "message", tag], cwd=tmp_path)

        return Git(tmp_path)

    return _
