# yubiOS advertisement kit

A dark-first, proof-aware campaign built from the canonical [`assets/logo.png`](../logo.png). The second pass keeps the original ads as `v1`, adds a more polished `v2`, and provides true 2× exports for both sets.

Every ad remains visibly marked `EXPERIMENTAL` or `PRE-LAUNCH`. The campaign invites technical review; it does not claim production readiness.

## Folder layout

| Folder | Contents |
|---|---|
| [`v1/`](v1/) | Original standard-size PNG exports. |
| [`v2/`](v2/) | Revised standard-size PNG exports with refreshed visuals and less repetitive copy. |
| [`v1-upscaled/`](v1-upscaled/) | New 2× renders of the original SVG layouts. |
| [`v2-upscaled/`](v2-upscaled/) | New 2× renders of the revised layouts. |
| [`source/v1/`](source/v1/) | Original editable SVG layouts and penguin foundation. |
| [`source/v2/`](source/v2/) | Revised SVG layouts, generated background foundations, and the exact prompt set. |

The obsolete hash-named kit archive was removed so the live folders, source files, and renderer remain the single organized source of truth.

## Recommended v2 exports

| Placement | Standard export | 2× export | Revised headline |
|---|---|---|---|
| Social square | [`1080 × 1080`](v2/yubios-ad-square-1080x1080.png) | [`2160 × 2160`](v2-upscaled/yubios-ad-square-2160x2160.png) | Hold the key. Verify the trust chain. |
| Social landscape / link preview | [`1200 × 628`](v2/yubios-ad-landscape-1200x628.png) | [`2400 × 1256`](v2-upscaled/yubios-ad-landscape-2400x1256.png) | Your machine. Your key. Verify the chain. |
| Medium rectangle | [`300 × 250`](v2/yubios-ad-medium-rectangle-300x250.png) | [`600 × 500`](v2-upscaled/yubios-ad-medium-rectangle-600x500.png) | Trust starts with your key. |
| Leaderboard | [`728 × 90`](v2/yubios-ad-leaderboard-728x90.png) | [`1456 × 180`](v2-upscaled/yubios-ad-leaderboard-1456x180.png) | Hold the key. Verify the chain. |
| Skyscraper | [`160 × 600`](v2/yubios-ad-skyscraper-160x600.png) | [`320 × 1200`](v2-upscaled/yubios-ad-skyscraper-320x1200.png) | Hold the key. Verify the chain. |
| Linux community banner | [`970 × 250`](v2/yubios-ad-linux-penguin-banner-970x250.png) | [`1940 × 500`](v2-upscaled/yubios-ad-linux-penguin-banner-1940x500.png) | Linux®, meet trust in your hands. |

The matching v1 files use the same standard filenames under [`v1/`](v1/); their 2× filenames are listed under [`v1-upscaled/`](v1-upscaled/).

## Rebuild the exports

The renderer requires Inkscape and ImageMagick. From the repository root, run:

```sh
assets/ads/source/render-ads.sh
```

The normal run preserves the checked-in v1 standard exports, regenerates every v1 2× export, and regenerates every v2 standard and 2× export. To deliberately rebuild the v1 standard exports too:

```sh
RENDER_V1_STANDARD=1 assets/ads/source/render-ads.sh
```

The renderer composites the canonical project logo after SVG rasterization, preserving the existing mark rather than redrawing it. The v2 image-generation outputs are background foundations only; all campaign wording, status labels, links, and legal text remain deterministic SVG content. The exact built-in generation prompts are recorded in [`source/v2/PROMPTS.md`](source/v2/PROMPTS.md).

## v2 alt text

- **Square:** yubiOS logo over a dark neon linked-chain design with the words “Hold the key. Verify the trust chain.” Experimental, pre-launch open-source project.
- **Landscape:** wide dark yubiOS ad with neon chain links and the words “Your machine. Your key. Verify the chain.”
- **Medium rectangle:** compact neon yubiOS ad reading “Trust starts with your key.”
- **Leaderboard:** wide dark yubiOS banner reading “Hold the key. Verify the chain.”
- **Skyscraper:** tall yubiOS ad reading “Hold the key. Verify the chain.” over a vertical neon link motif.
- **Linux banner:** a friendly penguin holding a generic glowing hardware key beside the words “Linux, meet trust in your hands.”

## Campaign guardrails

- Keep `EXPERIMENTAL` / `PRE-LAUNCH` visible. These ads describe a direction and invite review.
- The campaign is for an independent community project. It must not imply affiliation with, sponsorship by, or endorsement from Yubico.
- Preserve the canonical logo without recoloring or regenerating it.
- Keep claims aligned with [`PR.md`](../../PR.md): user-held keys, verifiable structure, explicit platform boundaries, and evidence published in the open.
- Complete the name, logo, and trademark review tracked in `PR.md` before paid placement or a broad launch.

## Linux and penguin attribution

The Linux banner uses `Linux®` on first prominent mention and includes the requested trademark legend. The Linux Foundation states that Linux is a registered trademark of Linus Torvalds and directs Tux usage questions to Larry Ewing's page: [Linux mark guidance](https://www.linuxfoundation.org/legal/the-linux-mark) and [Linux 2.0 Penguins](https://isc.tamu.edu/~lewing/linux/).

The banner contains a newly rendered penguin illustration, not Larry Ewing's original bitmap. The concept remains credited to Larry Ewing and The GIMP in the source and exports.
