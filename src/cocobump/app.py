import sys
from pathlib import Path
from typing import Optional, Tuple

import click

from .changelog import ChangeLog
from .configs import ProjectConfig, UpdateConfig
from .constants import INITIAL_RELEASE_COMMIT
from .enums import ChangeLogTypeEnum
from .git import Git
from .versions import Version


def echo(*values) -> None:
    print(*values, file=sys.stderr)


def create_update_config(changelog: ChangeLog) -> UpdateConfig:
    kwargs = {
        "is_breaking_change": False,
        "is_minor_change": False,
        "is_micro_change": False,
        "is_pre_release": False,
    }

    if changelog.has_breaking_change:
        kwargs["is_breaking_change"] = True
    elif changelog.has_minor_change:
        kwargs["is_minor_change"] = True
    else:
        kwargs["is_micro_change"] = True

    return UpdateConfig(**kwargs)


def run(project_config: ProjectConfig, git: Git, strict: bool) -> Tuple[Version, ChangeLog]:

    current_tag = git.retrieve_last_tag_or_none()

    echo("Current tag:", current_tag)

    current_version: Optional[Version] = None
    if current_tag is not None:
        current_version = Version.from_tag(current_tag, config=project_config)

    echo(
        "Current version:",
        current_version.format(config=project_config) if current_version else "-",
    )

    if current_tag is not None and current_version is not None:
        git_commits = git.list_commits(current_tag)
        changelog = ChangeLog.from_git_commits(git_commits, skip_failed=not strict)
        if not git_commits or len(changelog.commits) == 0:
            raise ValueError("No commits found after latest tag")

        update_config = create_update_config(changelog)
        next_version = current_version.update(update_config)
    else:
        git_commits = git.list_commits(None)
        next_version = Version.from_tag("v1.0.0", config=project_config)
        changelog = ChangeLog.from_git_commits(git_commits, skip_failed=not strict)

    return next_version, changelog


@click.command()
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

    By default non-CC commits are allowed. Use the `--strict` flag."""

    project_config = ProjectConfig.from_path(project_path)
    git = Git(project_config.path)

    try:
        next_version, changelog = run(project_config, git, strict)
    except Exception as e:
        ctx.fail(e)

    formatted_next_version = next_version.format(config=project_config)
    echo("Next version:", formatted_next_version)

    formatted_changelog = changelog.format(
        changelog_type=ChangeLogTypeEnum.git_commit,
        format_type=project_config.changelog_format_type_git,
    )
    echo("Changelog:\n", formatted_changelog)

    echo("Printing next version to stdout")
    print(formatted_next_version)


@click.command()
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

    By default non-CC commits are allowed. Use the `--strict` flag."""

    project_config = ProjectConfig.from_path(project_path)
    git = Git(project_config.path)

    try:
        next_version, changelog = run(project_config, git, strict)
    except Exception as e:
        ctx.fail(e)

    formatted_next_version = next_version.format(config=project_config)
    echo("Next version:", formatted_next_version)
    formatted_changelog = changelog.format(
        changelog_type=ChangeLogTypeEnum.git_commit,
        format_type=project_config.changelog_format_type_git,
    )

    echo("Printing changelog to stdout")
    print(formatted_changelog)
