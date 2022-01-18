from typing import Collection

from semver import VersionInfo as Version

from convbump.conventional import CommitType, ConventionalCommit

DEFAULT_FIRST_VERSION = Version(major=0, minor=1, patch=0)


def get_next_version(
    current_version: Version, conventional_commits: Collection[ConventionalCommit]
) -> Version:
    breaking_change = any(commit for commit in conventional_commits if commit.is_breaking)
    minor_change = any(
        commit for commit in conventional_commits if commit.commit_type == CommitType.FEAT
    )
    patch_change = any(
        commit for commit in conventional_commits if commit.commit_type != CommitType.FEAT
    )

    if breaking_change:
        return current_version.bump_major()
    elif minor_change:
        return current_version.bump_minor()
    elif patch_change:
        return current_version.bump_patch()
    else:
        return current_version
