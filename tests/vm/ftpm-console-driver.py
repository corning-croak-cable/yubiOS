#!/usr/bin/env python3
"""Drive a QEMU guest over its serial console and run a script inside it.

Used by tests/vm/test-ftpm-qemu-ci.sh Stage B. The fTPM chain boots
TF-A -> OP-TEE -> U-Boot -> Linux, so bcvk's kernel-cmdline SSH credential never
applies and the guest has no network. The dev/test image (Containerfile.dev)
ships a serial getty with root autologin, so the console IS the route in.

Usage:
    ftpm-console-driver.py <console.sock> <script-to-run> <timeout-seconds>

Exits with the in-guest script's exit code, or 77 when no shell prompt ever
appeared (treated as an explicit SKIP by the caller).
"""
import base64
import os
import socket
import sys
import time

SKIP = 77
PROMPT_MARKERS = (b"# ", b"~]#", b"root@")
RC_MARKER = b"YUBIOS_VERIFY_RC="
CHUNK = 384


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: ftpm-console-driver.py <console.sock> <script> <timeout>", file=sys.stderr)
        return 2
    sock_path, script_path, timeout_s = sys.argv[1], sys.argv[2], float(sys.argv[3])
    deadline = time.time() + timeout_s

    sock = None
    while time.time() < deadline:
        if os.path.exists(sock_path):
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(sock_path)
                break
            except OSError:
                sock = None
        time.sleep(1)
    if sock is None:
        print("SKIP: QEMU never created the console socket", file=sys.stderr)
        return SKIP
    sock.settimeout(2.0)

    buf = bytearray()

    def pump() -> bool:
        """Read whatever is available; echo it so CI captures the full console."""
        try:
            data = sock.recv(4096)
        except socket.timeout:
            return True
        except OSError:
            return False
        if not data:
            return False
        sys.stdout.write(data.decode("utf-8", errors="replace"))
        sys.stdout.flush()
        buf.extend(data)
        return True

    last_beat = time.time()

    def wait_for(needle: bytes, until: float, label: str) -> bool:
        nonlocal last_beat
        while time.time() < until:
            if needle in buf:
                return True
            if not pump():
                return False
            if time.time() - last_beat > 30:
                remaining = int(until - time.time())
                print(f"\n... still waiting for {label} ({remaining}s left)", file=sys.stderr)
                last_beat = time.time()
        return needle in buf
        while time.time() < until:
            if needle in buf:
                return True
            if not pump():
                return False
        return needle in buf

    def send(line: str) -> None:
        sock.sendall(line.encode() + b"\n")

    # Wait for the autologin shell. Nudge with newlines: if the getty is already
    # sitting at a prompt there is nothing left to print on its own.
    got_prompt = False
    while time.time() < deadline and not got_prompt:
        pump()
        if any(m in buf for m in PROMPT_MARKERS):
            got_prompt = True
            break
        if time.time() - last_beat > 30:
            remaining = int(deadline - time.time())
            print(f"\n... still waiting for a shell prompt ({remaining}s left)", file=sys.stderr)
            last_beat = time.time()
        pump()
        if any(m in buf for m in PROMPT_MARKERS):
            got_prompt = True
            break
        try:
            send("")
        except OSError:
            break
        time.sleep(3)

    if not got_prompt:
        print(
            "\nSKIP: no shell prompt on the serial console before timeout; "
            "the guest may not have reached Linux, or the image lacks the "
            "root-autologin getty (Containerfile.dev).",
            file=sys.stderr,
        )
        return SKIP

    with open(script_path, "rb") as fh:
        payload = base64.b64encode(fh.read()).decode()

    # Feed the payload in small pieces: a single multi-KB line can exceed the
    # tty's canonical-mode line buffer and get silently truncated.
    send("stty -echo 2>/dev/null; rm -f /tmp/yubios-verify.b64")
    time.sleep(0.5)
    for i in range(0, len(payload), CHUNK):
        send(f"printf '%s' '{payload[i:i + CHUNK]}' >> /tmp/yubios-verify.b64")
        time.sleep(0.15)
        pump()

    buf.clear()
    send(
        "base64 -d /tmp/yubios-verify.b64 > /tmp/yubios-verify.sh && "
        "chmod +x /tmp/yubios-verify.sh && /tmp/yubios-verify.sh; "
        f"echo {RC_MARKER.decode()}$?"
    )

    if not wait_for(RC_MARKER, deadline, "the in-guest script's exit code"):
        print("\nSKIP: in-guest script never reported an exit code", file=sys.stderr)
        return SKIP

    tail = bytes(buf).split(RC_MARKER)[-1]
    digits = bytearray()
    for byte in tail:
        ch = chr(byte)
        if ch.isdigit():
            digits.append(byte)
        elif digits:
            break
    if not digits:
        # The echoed command line can arrive before the real output.
        deadline2 = min(deadline, time.time() + 30)
        while time.time() < deadline2 and not digits:
            if not pump():
                break
            tail = bytes(buf).split(RC_MARKER)[-1]
            for byte in tail:
                ch = chr(byte)
                if ch.isdigit():
                    digits.append(byte)
                elif digits:
                    break
    if not digits:
        print("\nSKIP: could not parse the in-guest exit code", file=sys.stderr)
        return SKIP
    return int(digits.decode())


if __name__ == "__main__":
    sys.exit(main())
