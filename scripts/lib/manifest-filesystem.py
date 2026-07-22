#!/usr/bin/env python3

"""Emit a canonical JSON-lines manifest for a mounted filesystem tree."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record filesystem contents and intended POSIX metadata."
    )
    parser.add_argument("root", type=Path)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(root: Path) -> list[tuple[str, Path, os.stat_result]]:
    entries: list[tuple[str, Path, os.stat_result]] = [(".", root, root.lstat())]

    def visit(directory: Path, relative: str) -> None:
        with os.scandir(directory) as stream:
            children = sorted(stream, key=lambda entry: os.fsencode(entry.name))
        for child in children:
            child_relative = child.name if relative == "." else f"{relative}/{child.name}"
            child_path = directory / child.name
            status = child.stat(follow_symlinks=False)
            entries.append((child_relative, child_path, status))
            if stat.S_ISDIR(status.st_mode):
                visit(child_path, child_relative)

    visit(root, ".")
    return entries


def file_type(mode: int) -> str:
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISCHR(mode):
        return "char-device"
    if stat.S_ISBLK(mode):
        return "block-device"
    if stat.S_ISFIFO(mode):
        return "fifo"
    if stat.S_ISSOCK(mode):
        return "socket"
    return "unknown"


def read_xattrs(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for name in sorted(
        os.listxattr(path, follow_symlinks=False), key=os.fsencode
    ):
        value = os.getxattr(path, name, follow_symlinks=False)
        values[name] = base64.b64encode(value).decode("ascii")
    return values


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"filesystem root does not exist: {root}")

    entries = collect(root)
    hardlinks: dict[tuple[int, int], list[str]] = {}
    for relative, _path, status in entries:
        if stat.S_ISREG(status.st_mode) and status.st_nlink > 1:
            hardlinks.setdefault((status.st_dev, status.st_ino), []).append(relative)
    hardlink_first = {
        identity: sorted(paths, key=os.fsencode)[0]
        for identity, paths in hardlinks.items()
    }
    digest_cache: dict[tuple[int, int], str] = {}

    print(
        json.dumps(
            {"kind": "yubiOS-root-filesystem-manifest", "schema": 1},
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    for relative, path, status in entries:
        kind = file_type(status.st_mode)
        record: dict[str, object] = {
            "gid": status.st_gid,
            "mode": f"{stat.S_IMODE(status.st_mode):04o}",
            "mtime_ns": status.st_mtime_ns,
            "path": relative,
            "type": kind,
            "uid": status.st_uid,
            "xattrs": read_xattrs(path),
        }
        if kind == "file":
            identity = (status.st_dev, status.st_ino)
            digest = digest_cache.get(identity)
            if digest is None:
                digest = sha256(path)
                digest_cache[identity] = digest
            record["sha256"] = digest
            record["size"] = status.st_size
            first = hardlink_first.get(identity)
            if first is not None and first != relative:
                record["hardlink_to"] = first
        elif kind == "symlink":
            record["target"] = os.readlink(path)
        elif kind in {"char-device", "block-device"}:
            record["major"] = os.major(status.st_rdev)
            record["minor"] = os.minor(status.st_rdev)
        print(json.dumps(record, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OSError as error:
        print(f"filesystem-manifest: {error}", file=sys.stderr)
        raise SystemExit(1) from error
