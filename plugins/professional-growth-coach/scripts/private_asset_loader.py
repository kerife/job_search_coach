#!/usr/bin/env python3
"""Read renderer assets only from regular files inside the plugin package."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Iterable


class PrivateAssetError(OSError):
    """Raised when a renderer asset is not a regular package-local file."""


CANONICAL_RENDERER_ASSETS = (
    "assets/executive-career-dossier-v1.html",
    "assets/executive-career-dossier-v1.css",
    "assets/executive-career-dossier-v2.css",
    "assets/career-market-learning-dossier-v1.css",
    "assets/recruiter-practice-session-v1.html",
    "assets/recruiter-practice-session-v1.css",
    "assets/private-recruiter-reply-triage-v1.html",
    "assets/private-recruiter-reply-triage-v1.css",
    "assets/private-recruiter-followthrough-checkpoint-v1.html",
    "assets/private-recruiter-followthrough-checkpoint-v1.css",
    "assets/private-recruiter-conversion-outcome-v1.html",
    "assets/private-recruiter-conversion-outcome-v1.css",
)


def _regular_package_path(plugin_root: Path, asset_path: Path) -> Path:
    root = Path(plugin_root)
    path = Path(asset_path)
    if not root.is_absolute() or not path.is_absolute():
        raise PrivateAssetError("renderer asset input must be a regular file")
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise PrivateAssetError("renderer asset input must be a regular file") from exc
    if any(component in {"", ".", ".."} for component in relative.parts):
        raise PrivateAssetError("renderer asset input must be a regular file")
    current = root
    if current.is_symlink():
        raise PrivateAssetError("renderer asset input must be a regular file")
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise PrivateAssetError("renderer asset input must be a regular file")
    try:
        status = current.stat(follow_symlinks=False)
    except OSError as exc:
        raise PrivateAssetError("renderer asset input must be a regular file") from exc
    if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
        raise PrivateAssetError("renderer asset input must be a regular file")
    return current


def read_private_asset(
    plugin_root: Path,
    asset_path: Path,
    label: str = "renderer asset",
) -> str:
    """Read a UTF-8 asset after enforcing the package-local regular-file boundary."""

    del label
    path = _regular_package_path(plugin_root, asset_path)
    root = Path(plugin_root)
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise PrivateAssetError("renderer asset input must be a regular file") from exc
    if not relative.parts:
        raise PrivateAssetError("renderer asset input must be a regular file")

    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    if not no_follow or not directory_flag:
        raise PrivateAssetError("renderer asset input must be a regular file")
    current_fd: int | None = None
    leaf_fd: int | None = None
    try:
        # Open each directory component and retain its descriptor.  This keeps
        # the final read anchored to the package even if a pathname is swapped
        # after _regular_package_path() has returned.
        current_fd = os.open(
            os.fspath(root),
            os.O_RDONLY | directory_flag | no_follow,
        )
        for component in relative.parts[:-1]:
            next_fd = os.open(
                component,
                os.O_RDONLY | directory_flag | no_follow,
                dir_fd=current_fd,
            )
            old_fd = current_fd
            current_fd = next_fd
            os.close(old_fd)

        leaf_fd = os.open(
            relative.parts[-1],
            os.O_RDONLY | no_follow,
            dir_fd=current_fd,
        )
        status = os.fstat(leaf_fd)
        if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
            raise PrivateAssetError("renderer asset input must be a regular file")

        stream = os.fdopen(leaf_fd, "rb")
        leaf_fd = None
        with stream:
            return stream.read().decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise PrivateAssetError("renderer asset input must be a regular file") from exc
    finally:
        if leaf_fd is not None:
            try:
                os.close(leaf_fd)
            except OSError:
                pass
        if current_fd is not None:
            try:
                os.close(current_fd)
            except OSError:
                pass


def validate_asset_paths(
    plugin_root: Path,
    relative_paths: Iterable[str] = CANONICAL_RENDERER_ASSETS,
) -> list[str]:
    errors: list[str] = []
    root = Path(plugin_root)
    for relative in relative_paths:
        try:
            read_private_asset(root, root / relative)
        except PrivateAssetError:
            errors.append(f"{relative}: renderer asset input must be a regular file")
    return errors
