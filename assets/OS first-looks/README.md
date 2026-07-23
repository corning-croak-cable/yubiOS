# yubiOS OS first-look concepts

These 3840 x 2160 PNGs are design explorations, not screenshots of a shipped
interface and not proof of implemented behavior. The repository currently has a
GNOME-on-Wayland desktop profile; these images explore how that profile could
communicate yubiOS identity and owner-held trust. Each original is preserved
alongside purpose-built light- and dark-mode variants.

| Original | Light mode | Dark mode | Concept |
|---|---|---|---|
| `yubios-gnome-overview-concept-4k.png` | `yubios-gnome-overview-concept-4k-light.png` | `yubios-gnome-overview-concept-4k-dark.png` | GNOME Activities overview with a yubiOS wallpaper and restrained shell chrome. |
| `yubios-owner-key-enrollment-concept-4k.png` | `yubios-owner-key-enrollment-concept-4k-light.png` | `yubios-owner-key-enrollment-concept-4k-dark.png` | Four-step owner-key enrollment for Secure Boot, disk unlock, SSH, and login/sudo. |
| `yubios-system-trust-concept-4k.png` | `yubios-system-trust-concept-4k-light.png` | `yubios-system-trust-concept-4k-dark.png` | Settings-style firmware, boot-image, and owner-key status view. |

The theme variants retain the same task hierarchy and evidence-bounded status
language while adapting shell chrome, surface hierarchy, wallpaper luminance,
icon contrast, and text contrast for their intended viewing mode.

The token shown in the enrollment concept is deliberately generic and
unbranded. The concepts do not imply affiliation with or endorsement by Yubico,
GNOME, or another vendor. Any production UI must remain evidence-bounded and
must not claim verification states the running system cannot prove.

The full prompts and reference roles are recorded in
[`../visual-generation-prompts-2026-07-22.md`](../visual-generation-prompts-2026-07-22.md).
