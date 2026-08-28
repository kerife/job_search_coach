"""Descriptor-anchored reads for candidate-supplied private JSON inputs."""

from __future__ import annotations

import errno
import os
import stat
from pathlib import Path


class PrivateInputError(OSError):
    """A bounded private-input read failed for a known, safe reason."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _trusted_system_alias(absolute: str) -> str:
    parts = Path(absolute).parts
    if len(parts) > 1 and parts[1] in {"tmp", "var"}:
        component = parts[1]
        alias = os.path.join(os.sep, component)
        if os.path.islink(alias) and os.path.realpath(alias) == os.path.join(os.sep, "private", component):
            suffix = os.path.join(*parts[2:]) if len(parts) > 2 else ""
            return os.path.join(os.sep, "private", component, suffix)
    return absolute


def _open_parent(path: Path, nofollow: int, directory_flag: int) -> tuple[int, str]:
    absolute = _trusted_system_alias(os.path.abspath(os.fspath(path)))
    parent = Path(absolute).parent
    base_flags = os.O_RDONLY | directory_flag | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(os.sep, base_flags)
    try:
        for component in parent.parts[1:]:
            if component in {"", ".", ".."}:
                raise PrivateInputError("unavailable")
            next_descriptor: int | None = None
            try:
                next_descriptor = os.open(
                    component,
                    base_flags | nofollow,
                    dir_fd=descriptor,
                )
                if not stat.S_ISDIR(os.fstat(next_descriptor).st_mode):
                    raise PrivateInputError("unavailable")
                old_descriptor = descriptor
                descriptor = next_descriptor
                next_descriptor = None
                os.close(old_descriptor)
            except OSError as error:
                if error.errno == errno.ELOOP:
                    raise PrivateInputError("symlink") from error
                raise PrivateInputError("unavailable") from error
            finally:
                if next_descriptor is not None:
                    try:
                        os.close(next_descriptor)
                    except OSError:
                        pass
        return descriptor, Path(absolute).name
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def read_bounded_bytes(path: Path, max_bytes: int) -> bytes:
    """Read a regular file without following any user-controlled component."""

    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    if not nofollow or not directory_flag:
        raise PrivateInputError("unsupported")

    parent_descriptor, filename = _open_parent(path, nofollow, directory_flag)
    leaf_descriptor: int | None = None
    try:
        flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
        try:
            leaf_descriptor = os.open(filename, flags, dir_fd=parent_descriptor)
        except OSError as error:
            if error.errno == errno.ELOOP:
                raise PrivateInputError("symlink") from error
            raise PrivateInputError("unavailable") from error
        metadata = os.fstat(leaf_descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise PrivateInputError("unavailable")
        if metadata.st_nlink != 1:
            raise PrivateInputError("hardlink")
        if metadata.st_size > max_bytes:
            raise PrivateInputError("too_large")
        contents = bytearray()
        while True:
            chunk = os.read(leaf_descriptor, min(8192, max_bytes + 1 - len(contents)))
            if not chunk:
                break
            contents.extend(chunk)
            if len(contents) > max_bytes:
                raise PrivateInputError("too_large")
        return bytes(contents)
    except PrivateInputError:
        raise
    except OSError as error:
        raise PrivateInputError("unavailable") from error
    finally:
        if leaf_descriptor is not None:
            try:
                os.close(leaf_descriptor)
            except OSError:
                pass
        try:
            os.close(parent_descriptor)
        except OSError:
            pass
