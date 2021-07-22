import subprocess
from pathlib import Path
from typing import Optional, Tuple

import pytest

from cocobump.git import Git

CommitTuple = Tuple[str, Optional[str], str]
TagTuple = Tuple[str, str]


@pytest.fixture()
def create_git_commit():
    def factory(path: Path, commit: CommitTuple) -> None:
        file_path, content, message = commit

        (path / file_path).write_text(content or "")

        subprocess.check_call(["git", "add", "."], cwd=path)
        subprocess.check_call(["git", "commit", "-m", message], cwd=path)

    return factory


@pytest.fixture()
def create_git_repository(tmpdir, create_git_commit, create_git_tag):
    def factory(*commits: CommitTuple, tag: TagTuple = None) -> Git:
        path = Path(tmpdir)

        subprocess.check_call(["git", "init"], cwd=path)

        for commit in commits:
            create_git_commit(path, commit)

        if tag is not None:
            create_git_tag(path, *tag)

        return Git(path=path)

    return factory


@pytest.fixture()
def create_git_tag():
    def factory(path: Path, tag: str, message: str) -> None:
        subprocess.check_call(["git", "tag", "-a", tag, "-m", message], cwd=path)

    return factory
