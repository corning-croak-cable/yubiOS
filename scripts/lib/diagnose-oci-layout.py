#!/usr/bin/env python3
"""Explain byte differences between two OCI image-layout directories."""

from __future__ import annotations

import difflib
import hashlib
import json
import sys
import tarfile
from itertools import zip_longest
from pathlib import Path
from typing import Any, NoReturn


MAX_DIFF_LINES = 500


def die(message: str) -> NoReturn:
    raise SystemExit(f"diagnose-oci-layout: {message}")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def blob_path(layout: Path, digest: str) -> Path:
    algorithm, separator, value = digest.partition(":")
    if separator != ":" or algorithm != "sha256" or len(value) != 64:
        die(f"unsupported digest {digest!r}")
    return layout / "blobs" / algorithm / value


def resolve_image(layout: Path) -> tuple[Any, Any, Any]:
    index = read_json(layout / "index.json")
    manifests = index.get("manifests", [])
    if not manifests:
        die(f"{layout} has no image manifest")
    manifest = read_json(blob_path(layout, manifests[0]["digest"]))
    # BUILDKIT_MULTI_PLATFORM=1 emits a top-level OCI index whose descriptor
    # points to a second, platform-scoped index even for one architecture.
    # Follow that single-image chain until the actual manifest is reached.
    for _depth in range(8):
        if "config" in manifest and "layers" in manifest:
            break
        manifests = manifest.get("manifests", [])
        if not manifests:
            die(f"{layout} descriptor chain has no image manifest")
        manifest = read_json(blob_path(layout, manifests[0]["digest"]))
    else:
        die(f"{layout} descriptor chain is unexpectedly deep")
    config = read_json(blob_path(layout, manifest["config"]["digest"]))
    return index, manifest, config


def json_lines(value: Any) -> list[str]:
    return json.dumps(value, indent=2, sort_keys=True).splitlines(keepends=True)


def print_diff(label: str, before: Any, after: Any) -> None:
    lines = list(
        difflib.unified_diff(
            json_lines(before),
            json_lines(after),
            fromfile=f"a/{label}",
            tofile=f"b/{label}",
        )
    )
    if lines:
        print("".join(lines[:MAX_DIFF_LINES]), end="")
        if len(lines) > MAX_DIFF_LINES:
            print(f"... {len(lines) - MAX_DIFF_LINES} diff lines omitted")


def member_record(archive: tarfile.TarFile, member: tarfile.TarInfo) -> str:
    record: dict[str, Any] = {
        "name": member.name,
        "type": member.type.decode("ascii", errors="backslashreplace"),
        "mode": member.mode,
        "uid": member.uid,
        "gid": member.gid,
        "size": member.size,
        "mtime": member.mtime,
        "linkname": member.linkname,
        "uname": member.uname,
        "gname": member.gname,
        "pax_headers": member.pax_headers,
    }
    if member.isfile():
        extracted = archive.extractfile(member)
        if extracted is None:
            die(f"cannot read regular file {member.name!r}")
        digest = hashlib.sha256()
        for chunk in iter(lambda: extracted.read(1024 * 1024), b""):
            digest.update(chunk)
        record["content_sha256"] = digest.hexdigest()
    return json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"


def layer_records(path: Path) -> list[str]:
    with tarfile.open(path, mode="r:*") as archive:
        return [member_record(archive, member) for member in archive]


def print_layer_diff(index: int, a_path: Path, b_path: Path) -> None:
    try:
        a_records = layer_records(a_path)
        b_records = layer_records(b_path)
    except (OSError, tarfile.TarError) as error:
        print(f"layer[{index}]: cannot inspect tar members: {error}")
        return

    if a_records == b_records:
        print(
            f"layer[{index}]: file records match; difference is in compression "
            "or tar encoding"
        )
        return
    if sorted(a_records) == sorted(b_records):
        print(f"layer[{index}]: file records match after sorting; tar member order differs")
        return

    lines = list(
        difflib.unified_diff(
            sorted(a_records),
            sorted(b_records),
            fromfile=f"a/layer[{index}]",
            tofile=f"b/layer[{index}]",
            n=2,
        )
    )
    print("".join(lines[:MAX_DIFF_LINES]), end="")
    if len(lines) > MAX_DIFF_LINES:
        print(f"... {len(lines) - MAX_DIFF_LINES} layer diff lines omitted")


def main() -> int:
    if len(sys.argv) != 3:
        die(f"usage: {Path(sys.argv[0]).name} A_LAYOUT B_LAYOUT")
    a_layout, b_layout = map(Path, sys.argv[1:])
    a_index, a_manifest, a_config = resolve_image(a_layout)
    b_index, b_manifest, b_config = resolve_image(b_layout)

    print("=== OCI index diff ===")
    print_diff("index.json", a_index, b_index)
    print("=== OCI manifest diff ===")
    print_diff("manifest.json", a_manifest, b_manifest)
    print("=== OCI config diff ===")
    print_diff("config.json", a_config, b_config)

    print("=== Differing layer contents ===")
    for index, pair in enumerate(
        zip_longest(a_manifest.get("layers", []), b_manifest.get("layers", []))
    ):
        a_layer, b_layer = pair
        if a_layer == b_layer:
            continue
        if a_layer is None or b_layer is None:
            print(f"layer[{index}]: present in only one image")
            continue
        print(
            f"layer[{index}]: "
            f"a={a_layer['digest']} ({a_layer.get('size', '?')} bytes) "
            f"b={b_layer['digest']} ({b_layer.get('size', '?')} bytes)"
        )
        print_layer_diff(
            index,
            blob_path(a_layout, a_layer["digest"]),
            blob_path(b_layout, b_layer["digest"]),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
