#!/usr/bin/env python3
"""Extract the .cmdline PE section from a UKI (Unified Kernel Image).

Used by ci_test-vgpu-vm.yml composefs tamper (Negative 2) test.
UKI binaries embed the kernel command line in a PE section named ".cmdline"
(per systemd-boot/bootloader convention). dm-verity refusal tests parse
this section to discover the composefs=<sha512> digest that should be
tampered with.

Per bootc-uki-blsconfig-reference.md: BLSConfigType::EFI entries have
no `options` line; the cmdline lives in the UKI's PE section.
"""
import struct
import sys


def extract_cmdline(uki_path: str) -> str:
    with open(uki_path, "rb") as f:
        data = f.read()

    if len(data) < 0x40 or data[:2] != b"MZ":
        sys.exit(f"not a PE file: {uki_path}")

    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_off:pe_off + 4] != b"PE\0\0":
        sys.exit(f"not a PE file (bad sig): {uki_path}")

    # COFF header: Machine(2), NumSections(2), SizeOfOptionalHeader(2), Characteristics(2)
    coff = pe_off + 4
    num_sections = struct.unpack_from("<H", data, coff + 2)[0]
    size_opt = struct.unpack_from("<H", data, coff + 16)[0]

    # Optional header magic at pe_off+24: PE32=0x10b, PE32+=0x20b
    opt = coff + 20
    magic = struct.unpack_from("<H", data, opt)[0]
    _is_pe32plus = (magic == 0x20b)

    # Section table starts after optional header.
    sect = opt + size_opt
    for i in range(num_sections):
        s = sect + 40 * i
        name = data[s:s + 8].rstrip(b"\0").decode("latin-1")
        if name != ".cmdline":
            continue
        raw_off = struct.unpack_from("<I", data, s + 20)[0]
        raw_sz = struct.unpack_from("<I", data, s + 16)[0]
        chunk = data[raw_off:raw_off + raw_sz]
        # The cmdline section is NUL-terminated ASCII.
        nul = chunk.find(b"\0")
        if nul >= 0:
            chunk = chunk[:nul]
        return chunk.decode("utf-8", errors="replace").strip()

    sys.exit(f"no .cmdline section in PE file: {uki_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <uki_path>")
    sys.stdout.write(extract_cmdline(sys.argv[1]))


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L349",
  "file": "scripts/extract_uki_cmdline.py",
  "hypothesis": "scripts/extract_uki_cmdline.py covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 1,
    "missing_primitives": [
      "purpose",
      "examples",
      "constraints",
      "verification",
      "composition",
      "changelog",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "NO",
  "score": 6,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
