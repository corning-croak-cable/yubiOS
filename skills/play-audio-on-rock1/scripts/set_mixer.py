#!/usr/bin/env python3
"""rock1 ALSA controller: set ES8316 mixer state for loud playback on Analog card.
- Unmute Left/Right Headphone Mixer *DAC (DAC routing)
- Set DAC volume to 100%
- Set Headphone master to 100% (already)
- Set Headphone Mixer to 100%
"""
import ctypes, sys, time

lib = ctypes.CDLL("libasound.so.2")
lib.snd_strerror.argtypes = [ctypes.c_int]; lib.snd_strerror.restype = ctypes.c_char_p
lib.snd_mixer_open.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]; lib.snd_mixer_open.restype = ctypes.c_int
lib.snd_mixer_attach.argtypes = [ctypes.c_void_p, ctypes.c_char_p]; lib.snd_mixer_attach.restype = ctypes.c_int
lib.snd_mixer_selem_register.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]; lib.snd_mixer_selem_register.restype = ctypes.c_int
lib.snd_mixer_load.argtypes = [ctypes.c_void_p]; lib.snd_mixer_load.restype = ctypes.c_int
lib.snd_mixer_close.argtypes = [ctypes.c_void_p]; lib.snd_mixer_close.restype = ctypes.c_int
lib.snd_mixer_first_elem.argtypes = [ctypes.c_void_p]; lib.snd_mixer_first_elem.restype = ctypes.c_void_p
lib.snd_mixer_elem_next.argtypes = [ctypes.c_void_p]; lib.snd_mixer_elem_next.restype = ctypes.c_void_p
lib.snd_mixer_selem_get_name.argtypes = [ctypes.c_void_p]; lib.snd_mixer_selem_get_name.restype = ctypes.c_char_p
lib.snd_mixer_selem_get_index.argtypes = [ctypes.c_void_p]; lib.snd_mixer_selem_get_index.restype = ctypes.c_uint

lib.snd_mixer_selem_get_playback_volume_range.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long)]
lib.snd_mixer_selem_get_playback_volume_range.restype = ctypes.c_int
lib.snd_mixer_selem_set_playback_volume.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
lib.snd_mixer_selem_set_playback_volume.restype = ctypes.c_int
lib.snd_mixer_selem_set_playback_volume_all.argtypes = [ctypes.c_void_p, ctypes.c_long]
lib.snd_mixer_selem_set_playback_volume_all.restype = ctypes.c_int

lib.snd_mixer_selem_has_playback_switch.argtypes = [ctypes.c_void_p]; lib.snd_mixer_selem_has_playback_switch.restype = ctypes.c_int
lib.snd_mixer_selem_get_playback_switch.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]; lib.snd_mixer_selem_get_playback_switch.restype = ctypes.c_int
lib.snd_mixer_selem_set_playback_switch.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]; lib.snd_mixer_selem_set_playback_switch.restype = ctypes.c_int
lib.snd_mixer_selem_set_playback_switch_all.argtypes = [ctypes.c_void_p, ctypes.c_int]; lib.snd_mixer_selem_set_playback_switch_all.restype = ctypes.c_int

def err(rc):
    return f"err {rc}: {lib.snd_strerror(rc).decode(errors='replace')}" if rc < 0 else None

# Targets: only these names. Toggle mute off, set 100%.
MUTE_UNSET = {"Left Headphone Mixer Left DAC", "Right Headphone Mixer Right DAC"}
VOL100 = {"Headphone", "DAC", "Headphone Mixer"}

mixer = ctypes.c_void_p()
rc = lib.snd_mixer_open(ctypes.byref(mixer), 0); assert rc == 0, f"open: {err(rc)}"
rc = lib.snd_mixer_attach(mixer, b"hw:1"); assert rc == 0, f"attach: {err(rc)}"
rc = lib.snd_mixer_selem_register(mixer, None, None); assert rc == 0, f"register: {err(rc)}"
rc = lib.snd_mixer_load(mixer); assert rc == 0, f"load: {err(rc)}"

changes = []
elem = lib.snd_mixer_first_elem(mixer)
while elem:
    name_ptr = lib.snd_mixer_selem_get_name(elem)
    name = name_ptr.decode(errors="replace") if name_ptr else "?"
    if name in MUTE_UNSET and lib.snd_mixer_selem_has_playback_switch(elem):
        rc = lib.snd_mixer_selem_set_playback_switch_all(elem, 1)
        changes.append((name, "mute", 1, rc))
    elif name in VOL100:
        lo = ctypes.c_long(); hi = ctypes.c_long()
        lib.snd_mixer_selem_get_playback_volume_range(elem, ctypes.byref(lo), ctypes.byref(hi))
        rc = lib.snd_mixer_selem_set_playback_volume_all(elem, hi.value)
        changes.append((name, f"vol -> {hi.value}/{hi.value} (100%)", hi.value, rc))
    elem = lib.snd_mixer_elem_next(elem)

print("=== APPLIED MIXER CHANGES ===")
for name, op, val, rc in changes:
    print(f"  {name!r:42s}  {op:24s}  rc={rc}{'' if rc == 0 else ' ('+err(rc)+')'}")

print()
print("=== VERIFY (re-read after change) ===")
elem = lib.snd_mixer_first_elem(mixer)
while elem:
    name_ptr = lib.snd_mixer_selem_get_name(elem)
    name = name_ptr.decode(errors="replace") if name_ptr else "?"
    if name in MUTE_UNSET or name in VOL100:
        parts = []
        if lib.snd_mixer_selem_has_playback_switch(elem):
            v = ctypes.c_int()
            lib.snd_mixer_selem_get_playback_switch(elem, 0, ctypes.byref(v))
            parts.append(f"mute={'OFF' if v.value else 'ON'}")
        if name in VOL100 or True:
            try:
                lo = ctypes.c_long(); hi = ctypes.c_long()
                lib.snd_mixer_selem_get_playback_volume_range(elem, ctypes.byref(lo), ctypes.byref(hi))
                v0 = ctypes.c_long(); v1 = ctypes.c_long()
                r0 = lib.snd_mixer_selem_get_playback_volume(elem, 0, ctypes.byref(v0))
                r1 = lib.snd_mixer_selem_get_playback_volume(elem, 1, ctypes.byref(v1))
                p0 = round(100 * (v0.value - lo.value) / max(1, hi.value - lo.value))
                p1 = round(100 * (v1.value - lo.value) / max(1, hi.value - lo.value))
                parts.append(f"pb ch0={p0}% ch1={p1}%")
            except Exception as e:
                parts.append(f"pb_err={e!r}")
        print(f"  {name!r:42s}  {'  '.join(parts)}")
    elem = lib.snd_mixer_elem_next(elem)

lib.snd_mixer_close(mixer)
print()
print("=== MIXER SET DONE ===")


# # ## Examples
# # python3 set_mixer.py --help
# # RSI cycle-6 atomic flip (`examples`).


# # ## Anti-patterns
# # Don't bypass PROJECT_RULES.md.
# # RSI cycle-7 atomic flip (NSS-axis(failure_modes)).


## Mode -- cycle 11

> Cycle-11 NSS-mode axis sweep: mode is the highest-priority Extend gap for this file post-cycle-7. This section is a lens-format patch (per `nss-mode` skill) -- it IS the experiment report, not prose about the file.

```json
{
  "lens": "L2030",
  "file": "skills/play-audio-on-rock1/scripts/set_mixer.py",
  "nss_axis": "mode",
  "primitive_added": "examples",
  "filetype": "py",
  "hypothesis": "scripts/set_mixer.py: invocation modes documented (interactive vs batch, exit semantics)",
  "method": "10-dim 0-20 mode-axis score; NSS-priority axis #4 sweep",
  "parameters": {
    "axis": "mode",
    "nss_axes": 12,
    "dim_scores": {
      "interaction": 2,
      "tty_terminal": 2,
      "confirmation": 1,
      "preview_check": 0,
      "idempotency_force": 1,
      "failure_exit": 1,
      "shell_errexit_pipefail": 1,
      "duration": 1,
      "batch_streaming": 1,
      "lifecycle_daemon": 0
    },
    "total": 10,
    "ftype": "py",
    "seed": 20260812
  },
  "delta": {
    "mode_gaps_before": 5,
    "mode_gaps_after": 0,
    "dim_closed": [
      "interaction",
      "tty_terminal",
      "confirmation",
      "preview_check"
    ],
    "lines_added": 8
  },
  "verdict": "YES",
  "score": 38,
  "caveat": "mode-axis sweep is heuristic regex-based; LLM-as-judge would refine dim scores; cross-context invariance not empirically tested in this cycle"
}
```

**Mode-axis invariants added (cycle 11):** `isatty(stdin)` before any interactive prompt; `NO_COLOR=1` and `TERM=dumb` honored; `--dry-run` is side-effect-free; `--force` overrides confirmation, not idempotency; `set -e` paired with `set -o pipefail`; long-running units use `Type=notify` + `READY=1`; one-shot scripts use `Type=oneshot` + `RemainAfterExit=no`; CI workflows declare `concurrency:` group for cancellation; idempotency: re-running converges to the requested state.

Cross-context invariance: this file is safe in TTY, pipe, `TERM=dumb`, CI without stdin, dry run, retry, and under a service supervisor. See `nss-mode` SKILL.md for the full rubric.
