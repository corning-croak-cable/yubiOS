# yubiOS advertisement kit

A compact, dark-first campaign built from the repository's existing [`assets/logo.png`](../logo.png). Every execution uses the project's proof-first positioning and carries an `EXPERIMENTAL` or `PRE-LAUNCH` status marker.

## Ready-to-use exports

| Asset | Dimensions | Intended placement | Headline |
|---|---:|---|---|
| `yubios-ad-square-1080x1080.png` | 1080 × 1080 | Social feed / community post | Put the owner back in the trust chain. |
| `yubios-ad-landscape-1200x628.png` | 1200 × 628 | Link preview / social landscape | Your machine. Your key. Your trust chain. |
| `yubios-ad-medium-rectangle-300x250.png` | 300 × 250 | Standard display rectangle | Trust starts with your key. |
| `yubios-ad-leaderboard-728x90.png` | 728 × 90 | Standard leaderboard | Put the owner back in the trust chain. |
| `yubios-ad-skyscraper-160x600.png` | 160 × 600 | Standard wide skyscraper | Own the key. Own the chain. |
| `yubios-ad-linux-penguin-banner-970x250.png` | 970 × 250 | Extra wide banner / Linux® community placement | Linux®, meet owner-held trust. |

Editable SVG layouts, the reproducible renderer, and the penguin illustration foundation are under [`source/`](source/). The renderer composites the canonical project logo after SVG rasterization, so the mark is preserved pixel-for-pixel rather than embedded or redrawn.

Regenerate every PNG from the repository root with:

```sh
assets/ads/source/render-ads.sh
```

## Alt text

- **Square:** yubiOS logo over a dark neon security-chain pattern with the words “Put the owner back in the trust chain.” Experimental, pre-launch open-source project.
- **Landscape:** dark yubiOS ad with a large neon-framed project logo and the words “Your machine. Your key. Your trust chain.”
- **Medium rectangle:** compact neon yubiOS ad reading “Trust starts with your key.”
- **Leaderboard:** wide dark yubiOS banner reading “Put the owner back in the trust chain.”
- **Skyscraper:** tall yubiOS ad reading “Own the key. Own the chain.” over a vertical neon-chain motif.
- **Penguin banner:** Linux penguin holding a glowing security key beside the yubiOS headline “Linux, meet owner-held trust.”

## Campaign guardrails

- Keep `EXPERIMENTAL` / `PRE-LAUNCH` visible. These ads describe a direction and invite review; they do not claim production readiness.
- The campaign is for an independent community project. It must not suggest affiliation with, sponsorship by, or endorsement from Yubico.
- Preserve the existing logo without recoloring or regenerating it.
- Keep claims aligned with [`PR.md`](../../PR.md): owner-held control, verifiable structure, explicit platform boundaries, and evidence published in the open.
- Complete the name, logo, and trademark review already tracked in `PR.md` before paid placement or a broad launch.

## Linux and penguin attribution

The penguin banner uses `Linux®` on first prominent mention and includes the requested trademark legend. The Linux Foundation states that Linux is a registered trademark of Linus Torvalds and directs Tux usage questions to Larry Ewing's page: [Linux mark guidance](https://www.linuxfoundation.org/legal/the-linux-mark) and [Linux 2.0 Penguins](https://isc.tamu.edu/~lewing/linux/).

The banner contains a newly rendered penguin illustration, not Larry Ewing's original bitmap. The concept is nevertheless credited to Larry Ewing and The GIMP in the source and export.

## Penguin foundation generation prompt

The foundation was generated with the built-in image-generation workflow. The repository logo was supplied only as a color and visual-energy reference; the exact logo was composited later in SVG.

> Create an ultra-wide, premium open-source cybersecurity banner foundation. Place one friendly, confident, chubby black-and-white Linux penguin with warm yellow beak and feet on the right 30–35% of a near-black canvas. The penguin holds a small, generic glowing security key with no branding. Add restrained magenta, violet, cyan, and acid-green rim light, abstract cryptographic chain rings, a subtle grid, and faint circuit traces. Preserve the left 60% as calm negative space. Use a sophisticated editorial 3D style, not childish clip art. No text, letters, numbers, logos, watermark, Yubico branding, extra characters, screens, guns, or generic shield/checkmark imagery.
