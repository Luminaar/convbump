from typing import Collection

from semver import VersionInfo as Version

from convbump.conventional import (
    ConventionalCommit,
    VersionImpact,
    get_commit_version_impact,
)

DEFAULT_FIRST_VERSION = Version(major=0, minor=1, patch=0)


def get_next_version(
    current_version: Version, conventional_commits: Collection[ConventionalCommit]
) -> Version:
    """
    Calculate the next version based on conventional commits.
    Uses the unified version impact logic.
    """
    if not conventional_commits:
        return current_version

    # Find the highest version impact among all commits
    max_impact = VersionImpact.NONE
    for commit in conventional_commits:
        impact = get_commit_version_impact(commit.commit_type.value, commit.is_breaking)
        if impact.value > max_impact.value:
            max_impact = impact

    # Apply the version bump based on the highest impact
    if max_impact == VersionImpact.MAJOR:
        return current_version.bump_major()
    elif max_impact == VersionImpact.MINOR:
        return current_version.bump_minor()
    elif max_impact == VersionImpact.PATCH:
        return current_version.bump_patch()
    else:
        return current_version
