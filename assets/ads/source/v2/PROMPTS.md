# v2 background-generation prompts

The six v2 foundations were produced with the built-in image-generation workflow. Each call used the matching v1 export as an edit/composition reference; the first square result became the shared visual-style reference for the remaining formats.

The generated files contain no final campaign copy or canonical logo. Those elements are applied by the SVG layouts and [`../render-ads.sh`](../render-ads.sh).

## Square

Output: [`foundations/square-chain.png`](foundations/square-chain.png)

```text
Use case: ads-marketing
Asset type: background foundation for a square 1:1 open-source cybersecurity campaign ad
Input images: Image 1 is the edit target and composition/style reference.
Primary request: Remove every existing text element, letter, number, logo, badge, button, URL, and brand mark. Rebuild the image as a more polished second-pass background-only foundation for yubiOS.
Scene/backdrop: near-black navy-to-deep-purple field with a restrained technical grid, faint circuit traces, and one elegant abstract trust-chain / linked-loop structure concentrated along the right side and lower-right corner.
Style/medium: premium editorial 3D graphic design, crisp and modern, sophisticated open-source security aesthetic.
Composition/framing: square 1:1. Preserve calm, low-detail negative space across the left 62% and central-left area for later typography. Keep the visual energy on the right edge; do not place focal objects behind the future copy area.
Lighting/mood: controlled neon rim light, confident, technical, transparent, pre-launch rather than glossy enterprise advertising.
Color palette: near-black, deep indigo, neon magenta, restrained violet and cyan, tiny acid-green highlights.
Constraints: background only; keep the overall visual identity of the reference while improving depth, hierarchy, finish, and legibility. No text of any kind.
Avoid: letters, numbers, words, logos, watermarks, badges, UI, buttons, URLs, people, mascots, keys, product shots, generic shields, checkmarks, padlocks, or hacker clichés.
```

## Landscape

Output: [`foundations/landscape-chain.png`](foundations/landscape-chain.png)

```text
Use case: ads-marketing
Asset type: background foundation for a 1200×628 landscape open-source cybersecurity ad
Input images: Image 1 is the aspect-ratio and layout reference. Image 2 is the approved second-pass visual-style reference.
Primary request: Create a background-only yubiOS campaign foundation that matches Image 2's premium neon linked-chain language while fitting Image 1's wide layout. Remove and do not reproduce any text, letters, numbers, logo, badge, button, URL, or brand mark.
Scene/backdrop: near-black navy and deep indigo, subtle technical grid and faint circuit traces. One elegant glassy linked-loop trust-chain structure lives in the rightmost 35–40%, with restrained magenta, violet, cyan, and tiny acid-green rim lighting.
Composition/framing: exact wide landscape feel, approximately 1.91:1. Preserve calm low-detail negative space across the left 62% for later headline, subcopy, and call-to-action. Keep all bright focal detail on the right.
Style/medium: premium editorial 3D graphic design; sophisticated open-source security aesthetic; crisp but not sterile.
Constraints: improve depth and polish over Image 1, preserve the campaign palette, background only.
Avoid: any text, typography, symbols that resemble letters, logos, watermarks, badges, UI, buttons, URLs, people, mascots, keys, product shots, shields, checkmarks, padlocks, or hacker clichés.
```

## Medium rectangle

Output: [`foundations/medium-chain.png`](foundations/medium-chain.png)

```text
Use case: ads-marketing
Asset type: background foundation for a 300×250 medium-rectangle open-source cybersecurity ad
Input images: Image 1 is the aspect-ratio and layout reference. Image 2 is the approved second-pass visual-style reference.
Primary request: Create a text-free background-only yubiOS campaign foundation. Match Image 2's polished glassy neon linked-chain language while respecting Image 1's compact 6:5 composition. Remove and do not reproduce any existing text, letters, numbers, logo, badge, URL, or brand mark.
Scene/backdrop: near-black navy/deep-purple field, subtle technical grid and very faint circuit traces. Place one small elegant linked-loop structure high on the right edge, partially cropped, with restrained magenta/violet/cyan light and a tiny acid-green accent.
Composition/framing: approximately 6:5. Preserve quiet negative space across the left two-thirds and lower-left/middle for later typography. The bright motif must not compete with copy.
Style/medium: premium editorial 3D graphic design, clean open-source cybersecurity campaign, excellent small-size legibility.
Constraints: background only; maintain the campaign palette and improve finish.
Avoid: any text, letters, numbers, logos, watermarks, badges, UI, buttons, URLs, people, mascots, keys, product shots, shields, checkmarks, padlocks, hacker clichés.
```

## Leaderboard

Output: [`foundations/leaderboard-chain.png`](foundations/leaderboard-chain.png)

```text
Use case: ads-marketing
Asset type: background foundation for a 728×90 ultra-wide leaderboard ad
Input images: Image 1 is the exact ultra-wide layout/aspect reference. Image 2 is the approved second-pass visual-style reference.
Primary request: Create a background-only yubiOS campaign foundation that carries Image 2's polished glassy neon chain system into the very shallow Image 1 banner. Remove and do not reproduce text, letters, numbers, logo, badge, button, URL, or brand mark.
Scene/backdrop: near-black navy/deep-purple band with a subtle technical grid. Use a slender, elegant linked-loop arc or interlocking neon path through the lower middle and right background, restrained enough for later typography.
Composition/framing: preserve the approximately 8.1:1 ultra-wide leaderboard format. Keep the left 26%, middle 42%, and right 26% mostly calm and readable for logo, headline, and CTA overlays. Bright chain detail should remain thin, peripheral, and behind those zones.
Style/medium: premium editorial 3D graphic design, crisp at tiny display size, sophisticated open-source cybersecurity aesthetic.
Color palette: deep navy, indigo, magenta, violet, cyan, tiny acid-green edge accent.
Constraints: background only, highly legible when reduced to 728×90, no visual clutter.
Avoid: any text, letter-like symbols, numbers, logos, watermark, badges, UI, buttons, URLs, people, mascots, keys, products, shields, checkmarks, padlocks, hacker clichés.
```

## Skyscraper

Output: [`foundations/skyscraper-chain.png`](foundations/skyscraper-chain.png)

```text
Use case: ads-marketing
Asset type: background foundation for a 160×600 vertical skyscraper ad
Input images: Image 1 is the exact tall layout/aspect reference. Image 2 is the approved second-pass visual-style reference.
Primary request: Create a background-only yubiOS campaign foundation that adapts Image 2's refined glassy neon linked-chain language into Image 1's very tall narrow format. Remove and do not reproduce any text, letters, numbers, logo, badge, button, URL, or brand mark.
Scene/backdrop: near-black navy/deep-purple vertical field, sparse technical grid and faint circuit traces. A single elegant chain-link structure travels down the right edge and through the middle-lower background, partially cropped, with restrained magenta/violet/cyan light and tiny acid-green accents.
Composition/framing: preserve the approximately 1:3.75 tall skyscraper ratio. Keep the top 28% and central-left region low-detail for logo/status and stacked headline; reserve a calm bottom strip for CTA.
Style/medium: premium editorial 3D graphic design; sophisticated open-source cybersecurity campaign; crisp at 160 pixels wide.
Constraints: background only, strong depth but minimal clutter and excellent small-size readability.
Avoid: any text, letter-like marks, numbers, logos, watermarks, badges, UI, buttons, URLs, people, mascots, keys, product shots, shields, checkmarks, padlocks, hacker clichés.
```

## Linux community banner

Output: [`foundations/linux-penguin.png`](foundations/linux-penguin.png)

```text
Use case: ads-marketing
Asset type: background foundation for a 970×250 ultra-wide Linux community campaign banner
Input images: Image 1 is the aspect, mascot-placement, and campaign-context reference. Image 2 is the approved second-pass neon chain visual-style reference.
Primary request: Produce a polished second-pass, background-only banner foundation. Preserve the idea of one friendly, confident black-and-white Linux penguin on the right holding a small generic glowing hardware security key, but improve the rendering, lighting, material detail, and integration with Image 2's elegant glassy linked-chain environment. Remove and do not reproduce any text, letters, numbers, yubiOS logo, badge, URL, attribution, or brand mark.
Scene/backdrop: near-black navy/deep-indigo technical field with restrained grid and circuit traces. Behind and around the penguin, one refined neon trust-chain structure with magenta, violet, cyan, and tiny acid-green highlights.
Subject: exactly one original stylized Linux penguin, warm yellow beak and feet, friendly and technically confident, holding one small unbranded security key with a subtle magenta status light. Do not imitate or reproduce Larry Ewing's original bitmap.
Composition/framing: approximately 3.88:1 ultra-wide banner. Keep the left 58–60% calm, dark, and low-detail for later logo, status, headline, subcopy, and legal legend. Place the penguin fully within the rightmost 32–35%, with chain detail behind it and no bright spill into the left copy area.
Style/medium: sophisticated editorial 3D illustration, premium open-source security campaign, not childish clip art.
Constraints: background and mascot only; exact clean separation between calm copy area and subject; independent community-project tone.
Avoid: any text, letter-like marks, numbers, logos, watermarks, branded hardware, Yubico/YubiKey marks, extra characters, extra limbs, extra keys, screens, guns, generic shields, checkmarks, padlocks, hacker hoodies, or corporate stock imagery.
```
