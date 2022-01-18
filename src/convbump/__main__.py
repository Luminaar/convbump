import sys
from pathlib import Path
from typing import Tuple

import click
from semver import VersionInfo as Version

from convbump.conventional import ConventionalCommit, format_changelog

from .git import Git
from .version import DEFAULT_FIRST_VERSION, get_next_version


def echo(*values: str) -> None:
    print(*values, file=sys.stderr)


def _run(git: Git, strict: bool) -> Tuple[Version, str]:
    """Find the next version and generate a changelog from
    conventional commits."""

    tag, current_version = git.retrieve_last_version()
    if not current_version:
        echo("Using default first version")
        return DEFAULT_FIRST_VERSION, ""

    conventional_commits = []
    for commit in git.list_commits(tag):
        try:
            conventional_commits.append(ConventionalCommit.from_git_commit(commit))
        except ValueError:
            if not strict:
                continue
            else:
                raise

    if len(conventional_commits) == 0:
        raise ValueError("No commits found after the latest tag")

    next_version = get_next_version(current_version, conventional_commits)
    changelog = format_changelog(conventional_commits)

    return next_version, changelog


@click.group()
def convbump() -> None:
    """convbump is a simple tool to work with conventional commits.

    Use the `version` command to find the next version in your repository
    based on the conventional commits.

    Use the `changelog` command to generate a nicely formatted changelog
    (Github markdown compatible)."""


@convbump.command()
@click.pass_context
@click.option(
    "--project-path", default=".", type=click.Path(file_okay=False, exists=True, path_type=Path)
)
@click.option(
    "--strict", is_flag=True, default=False, help="Fail if non-Conventinal commits are found"
)
def version(ctx: click.Context, project_path: Path, strict: bool) -> None:
    """Calculate next version from Git history.

    Given a Git repository, this command will find the latest version tag and
    calculate the next version using the Conventional Commits (CC) specification.

    Calculated version will be printed out to STDOUT.

    By default non-CC commits are allowed. Use the `--strict` flag to fail
    if any non-CC commits are present."""

    git = Git(project_path)

    try:
        next_version, changelog = _run(git, strict)
    except ValueError as e:
        ctx.fail(e)  # type: ignore

    echo("Changes:")
    echo(changelog)
    echo("\nNext version:")
    print(next_version)


@convbump.command()
@click.pass_context
@click.option(
    "--project-path", default=".", type=click.Path(file_okay=False, exists=True, path_type=Path)
)
@click.option(
    "--strict", is_flag=True, default=False, help="Fail if non-Conventinal commits are found"
)
def changelog(ctx: click.Context, project_path: Path, strict: bool) -> None:
    """Create a ChangeLog from Git history.

    Given a Git repository, this command will find the latest version tag and
    generate a ChangeLog from Conventional Commits (CC).

    Generated ChangeLog will be printed out to STDOUT.

    By default non-CC commits are allowed. Use the `--strict` flag to fail
    if any non-CC commits are present."""

    git = Git(project_path)

    try:
        next_version, changelog = _run(git, strict)
    except ValueError as e:
        ctx.fail(e)  # type: ignore

    echo("Next version:", next_version)
    echo("\nChanges:")
    print(changelog)
