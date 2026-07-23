# Visual-generation prompts - 2026-07-22

The built-in OpenAI image-generation tool created the native compositions and
their purpose-built light- and dark-mode variants. ImageMagick exported the
selected logo concepts at 2048 x 2048 and the wide assets at 3840 x 2160. The
maintainer-supplied images were style, palette, texture, composition, and mood
references; they were not checked into this repository by this change.

## Logo concepts

### Linked bloom

References: `assets/logo.png`, `Icon.jpg`, `Bloom.jpg`, `Halo.jpg`, and
`Vloom.png`.

```text
Use case: logo-brand
Asset type: yubiOS new logo concept, square master
Primary request: Create an original, minimal emblem for yubiOS that fuses a blooming iris or flower with a subtle keyhole and linked trust-ring structure. The supplied images are style and mood references only; do not reproduce or collage them.
Input images: current yubiOS logo and Vloom are brand-history references; Icon, Bloom, and Halo are palette, texture, and radial-form references.
Style/medium: vector-friendly flat emblem with a restrained analog-glitch texture, crisp silhouette, balanced negative space, contemporary open-source operating-system identity.
Composition/framing: one centered symbol, generous margin, perfectly square, readable at favicon size.
Color palette: near-black ground, hot pink and violet core, cyan and acid-green accents, small off-white highlight.
Constraints: no text, no letters, no mockup, no hardware product, no trademarked shape, no Yubico branding, no watermark; original design only; strong scalable silhouette; polished high-resolution brand asset.
Avoid: photorealistic flower, noisy collage, skulls, shields, padlocks, generic cybersecurity clip art, gradients that destroy edge clarity.
```

### Owner orbit

References: `assets/logo.png`, `Halo.jpg`, `Waves.jpg`, and `Icon.jpg`.

```text
Use case: logo-brand
Asset type: yubiOS new logo concept, square master
Primary request: Create an original yubiOS emblem built from one bold orbital ring, a small owner-held center, and three interlocking petals that also read as a continuous trust chain. The supplied images are style and mood references only.
Input images: current logo is brand-history reference; Halo and Waves guide concentric geometry; Icon guides energetic edge texture.
Style/medium: minimal vector-friendly symbol, flat geometric color fields, subtle screen-print grain, strong silhouette and memorable negative space.
Composition/framing: single centered circular mark, generous square margins, clean favicon readability.
Color palette: black, electric cyan, hot pink, ultraviolet, one acid-green accent.
Constraints: no text, no letters, no mockup, no product, no real key, no keyhole, no shield, no padlock, no trademarked symbol, no Yubico branding, no watermark; original design only; polished high-resolution brand asset.
Avoid: photorealism, collage, excessive detail, generic cybersecurity icons, gradients that blur the silhouette.
```

### Trust tree

References: `assets/logo.png`, `Tree.jpg`, `Spikes.jpg`, `Bloom.jpg`, and
`Blue.jpg`.

```text
Use case: logo-brand
Asset type: yubiOS new logo concept, square master
Primary request: Create an original yubiOS emblem where a compact root system rises into a luminous abstract bloom, with exactly three branch paths joining into one crown to suggest firmware, immutable OS, and owner-held identity converging. References provide palette, organic motion, and analog texture only.
Style/medium: bold vector-friendly crest without a border, flat shapes with restrained etched/glitch texture, modern open-source operating-system identity.
Composition/framing: centered vertically symmetric mark with generous negative space, strong at 32px and dramatic at poster size.
Color palette: deep navy-black, cyan trunk, magenta and violet canopy, acid-green highlights, warm off-white center.
Constraints: no text, no letters, no mockup, no hardware product, no shield, no lock, no key silhouette, no trademarked mark, no Yubico branding, no watermark; original design only; polished high-resolution brand asset.
Avoid: literal tree illustration, landscape scene, fine twig detail, photorealism, clip art, noisy collage.
```

## OS first-look concepts

### GNOME overview

References: the generated aurora-ridge wallpaper, `assets/logo.png`, and the
generated owner-orbit concept.

```text
Use case: ui-mockup
Asset type: yubiOS OS first-look concept, 16:9 desktop screenshot
Primary request: Create a polished, plausible first-look of the yubiOS GNOME-on-Wayland desktop. Use Image 1 as the wallpaper foundation, Image 2 as the current small bloom emblem, and Image 3 only as a secondary visual-system reference.
Scene/backdrop: full-screen dark GNOME desktop with the mountain-halo wallpaper.
Style/medium: high-fidelity product UI mockup, calm and shippable rather than futuristic concept art.
Composition/framing: true 16:9 desktop capture; slim dark GNOME top bar; centered clock; subtle status icons; compact bottom dash opened in Activities overview; two clean workspace thumbnails; generous breathing room.
Text (verbatim): "Activities", "Jul 22  18:42"
Constraints: render only the exact text above; practical GNOME hierarchy; use generic open-source app icons with no third-party logos; small yubiOS bloom mark may appear once; no macOS dock, no Windows start menu, no watermark, no product ad, no hardware key.
Avoid: holograms, fake terminal code, dense widgets, glassmorphism everywhere, excessive neon, illegible microtext.
```

### Owner-key enrollment

References: the generated living-root wallpaper, `assets/logo.png`, and the
generated linked-bloom concept.

```text
Use case: ui-mockup
Asset type: yubiOS OS first-look concept, owner-key enrollment
Primary request: Create a polished GNOME initial-setup screen for yubiOS that presents the owner-held FIDO2 enrollment flow. Image 1 supplies the wallpaper palette; Image 2 is the current yubiOS emblem; Image 3 guides flower/keyhole motifs only.
Scene/backdrop: blurred dark bloom-circuit wallpaper behind one centered setup window.
Style/medium: high-fidelity GNOME/Adwaita-like desktop UI, practical and accessible, not science fiction.
Composition/framing: 16:9 screenshot; centered rounded dark window; left progress rail with four steps; right panel shows a generic unbranded USB/NFC security token and a simple touch indicator; one prominent magenta action button.
Text (verbatim): "Set up owner key", "Secure Boot", "Disk unlock", "SSH", "Login & sudo", "Touch your security key", "Continue"
Constraints: render the exact text cleanly with no extra prose; show all four steps once; generic unbranded token only; no Yubico logo or trademarked product design; strong contrast; no watermark.
Avoid: password fields, cloud account prompts, QR codes, padlock clip art, hacker imagery, tiny unreadable labels.
```

### System trust

References: the generated owner-rings wallpaper, `assets/logo.png`, and the
generated trust-tree concept.

```text
Use case: ui-mockup
Asset type: yubiOS OS first-look concept, system trust status
Primary request: Create a polished yubiOS settings panel that makes the verified boot and owner-key state legible. Image 1 supplies the cool ring palette, Image 2 is the current emblem, and Image 3 guides the living-root visual language.
Scene/backdrop: dark GNOME desktop with a subtle concentric-wave wallpaper and one foreground settings window.
Style/medium: high-fidelity GNOME/Adwaita-like system settings UI, restrained, trustworthy, accessible.
Composition/framing: 16:9 screenshot; left settings navigation; main panel with a clear vertical trust path of three large status cards connected by a thin line; each card has a small green verified dot; one compact details pane.
Text (verbatim): "System Trust", "Firmware", "Boot image", "Owner key", "Verified", "Details"
Constraints: render only the exact text above; practical desktop layout; no percentages or invented measurements; small yubiOS emblem once; no third-party logos, no watermark, no product marketing.
Avoid: shields, padlocks, threat meters, red alerts, dense terminal output, holographic UI, illegible tiny text.
```

## Wallpapers

### Aurora ridge

References: `Ararat.jpg`, `Everest.jpg`, and `Halo.jpg`.

```text
Use case: stylized-concept
Asset type: yubiOS desktop wallpaper, wide 16:9
Primary request: Create an original panoramic mountain landscape with a precise snow ridge beneath a translucent aurora-like trust halo. Use the references only for psychedelic color separation, grain, and panoramic energy.
Scene/backdrop: distant high mountain range under a deep pre-dawn sky.
Style/medium: polished analog-solarized landscape fused with restrained digital color fields; elegant, atmospheric, not a collage.
Composition/framing: true 16:9 wide wallpaper; low horizon; broad calm sky and uncluttered upper-left and upper-center space for GNOME UI.
Lighting/mood: luminous, sovereign, quiet, slightly otherworldly.
Color palette: deep navy and violet shadows, cyan snow, hot-pink aurora, sparing acid-green/gold highlights.
Constraints: text-free, no logo, no watermark, no people, no buildings, no flags; high-resolution desktop wallpaper; balanced contrast so white UI remains legible.
Avoid: oversharpened HDR, busy stars everywhere, neon clipping, literal copies of Mount Ararat or Everest photos.
```

### Owner rings

References: `Waves.jpg`, `Sphinx.jpg`, `Halo.jpg`, and `Coffee.jpg`.

```text
Use case: stylized-concept
Asset type: yubiOS desktop wallpaper, wide 16:9
Primary request: Create an original field of concentric glassy waves and nested trust rings, like a calm topographic ripple revealing a glowing owner-held core. References guide circular rhythm, analog grain, and saturated color only.
Scene/backdrop: abstract deep-space surface with softly layered rings.
Style/medium: high-end abstract desktop wallpaper, tactile painted/glass textures, controlled chromatic aberration.
Composition/framing: 16:9 landscape; primary ring slightly right of center; generous low-detail dark area on the left for desktop icons; no hard seam.
Lighting/mood: cool, calm, precise, immersive.
Color palette: midnight blue, cyan, lavender, magenta, off-white glow, tiny acid-green accents.
Constraints: no text, no letters, no logo, no watermark, no people, no product, no UI; high-resolution wallpaper; avoid visual noise at the top bar.
Avoid: literal eye, portal cliché, flat vector diagram, obvious lens flare, harsh white clipping.
```

### Living root

References: `Tree.jpg`, `Bloom.jpg`, `Icon.jpg`, and `Blue.jpg`.

```text
Use case: stylized-concept
Asset type: yubiOS desktop wallpaper, wide 16:9
Primary request: Create an original abstract bloom whose petals dissolve into branching circuit-like rivers, suggesting a living immutable system growing from one trusted root. Use references for palette, organic motion, and analog texture only.
Scene/backdrop: deep navy-black field with softly illuminated botanical-digital forms.
Style/medium: painterly macro abstraction with screen-print grain and delicate circuit traces, polished and cohesive.
Composition/framing: 16:9 landscape; bloom low and right of center; calm negative space across the upper third and left quarter for GNOME UI.
Lighting/mood: bioluminescent, resilient, contemplative.
Color palette: cyan roots, violet and hot-pink petals, emerald-to-acid-green edge light, subtle warm-white core.
Constraints: no text, no logo, no watermark, no literal computer hardware, no people, no insects; high-resolution desktop wallpaper.
Avoid: generic fractal, dense all-over noise, realistic flower photo, symmetry so rigid it looks like a logo.
```

### Nocturne bands

References: `Heim.jpg`, `Spikes.jpg`, `Turtle.jpg`, and `Fruit.jpg`.

```text
Use case: stylized-concept
Asset type: yubiOS desktop wallpaper, wide 16:9
Primary request: Create an original dark abstract architecture of curved stacked bands crossing a textured night field, with sparse luminous nodes and one concealed bloom-like pulse. References guide geometric distortion, scan texture, and color contrast only.
Scene/backdrop: nocturnal abstract space, no recognizable real building.
Style/medium: brutalist analog-glitch painting refined into a premium dark wallpaper; layered film grain, soft pigment blooms, restrained scan lines.
Composition/framing: 16:9 landscape; strong sweeping bands from lower-left toward upper-right; quiet central/top areas for GNOME shell; depth without clutter.
Lighting/mood: secure, mysterious, controlled, industrial-organic.
Color palette: near-black, bottle green, ultraviolet, cyan, hot-pink and ember-red accents.
Constraints: no text, no letters, no logo, no watermark, no faces, no people, no skull imagery, no recognizable building; high-resolution desktop wallpaper.
Avoid: horror, muddy blacks, noisy full-frame glitch, hard checkerboard seams, cyberpunk city cliché.
```

## Light- and dark-mode variant prompt set

Each original repository image was the sole edit target for its two variants.
The built-in image-generation tool used the following parameterized prompt
shape; the asset-specific direction and invariants below complete the prompt.

```text
Use case: precise-object-edit (lighting-weather where the change is explicitly time-of-day)
Asset type: yubiOS <asset>, <light-mode or dark-mode> variant
Input image: edit target; preserve the existing composition exactly.
Primary request: <theme direction below>
Constraints: <asset invariants below>; no added or removed subject matter; no text or watermark except the exact existing UI labels listed below.
```

### Logo theme variants

Shared invariants: preserve the symbol geometry, silhouette, proportions,
centered placement, generous margins, analog texture, and square composition;
no redesign, added or removed elements, text, letters, watermark, or mockup.

#### Linked bloom

- Light: replace black with a warm off-white to pale cool-gray ground; rebalance
  magenta, violet, cyan, acid-green, and cream slightly darker and richer so
  every ring, petal, keyhole, and grain-texture edge remains legible.
- Dark: use a subtly textured deep navy-black ground; lift violet and cyan
  midtones, control the cream highlight, and sharpen separation among petals,
  ring segments, and keyhole without neon clipping.
- Additional invariant: preserve every ring connection and the keyhole.

#### Owner orbit

- Light: replace black with a soft warm-white to pale cool-gray ground; deepen
  the cyan orbital ring, violet, magenta, and blue petals, and acid-green core
  for crisp light-theme contrast while retaining screen-print grain.
- Dark: use a deep blue-black ground; refine edge contrast around the orbital
  ring and three petals, retain the acid-green center, and moderate highlights
  for comfortable low-light use.
- Additional invariants: preserve the circular geometry, three interlocking
  petals, and central owner-held core.

#### Trust tree

- Light: replace navy-black with warm off-white to very pale blue-gray; deepen
  cyan roots and trunk, violet and magenta canopy, acid-green accents, and the
  warm center so fine branches retain their etched texture.
- Dark: use a deep blue-black ground with subtle tonal depth; lift cyan roots
  and violet canopy midtones, control magenta and acid-green accents, and
  protect the warm center from clipping.
- Additional invariants: preserve the vertically symmetric root-to-bloom
  geometry and exactly three joining branch paths.

### OS first-look theme variants

Shared invariants: preserve 16:9 framing, layout, spacing, UI hierarchy, and
existing subject placement; render only the listed text with no spelling
changes or extra copy; no redesign, new widgets, third-party logos, or
watermark.

#### GNOME overview

- Light: shift the mountain-halo wallpaper toward bright dawn with pale cyan
  and lavender sky, controlled magenta halo, and readable terrain; use
  restrained light Adwaita-like shell surfaces with dark icons and text.
- Dark: deepen the blue-black sky and terrain, reduce clipping in the magenta
  halo and snow, and improve separation of the top bar, workspace thumbnails,
  dash, and icons.
- Text: `"Activities"`, `"Jul 22  18:42"`.
- Additional invariants: preserve mountain and halo placement, top bar,
  workspace thumbnails, dash location, and icon positions; no macOS or Windows
  styling.

#### Owner-key enrollment

- Light: use a soft off-white centered window, pale cool-gray secondary
  surfaces, dark navy text, a high-contrast progress rail, and the same
  restrained magenta action button; brighten the blurred bloom-circuit
  wallpaper without making it busy.
- Dark: use richer blue-black surface hierarchy, improve text and progress-rail
  contrast, control the magenta button glow, and keep the generic token clearly
  separated without harsh highlights.
- Text: `"Set up owner key"`, `"Secure Boot"`, `"Disk unlock"`, `"SSH"`,
  `"Login & sudo"`, `"Touch your security key"`, `"Continue"`.
- Additional invariants: preserve the centered window, four-step progress rail,
  generic unbranded token, touch indicator, and button; no product logo,
  password field, or cloud prompt.

#### System Trust

- Light: use warm off-white main surfaces, pale cool-gray navigation and cards,
  dark navy text, restrained blue selection, and accessible green verified
  dots; brighten the wallpaper into pale cyan, lavender, and soft blue.
- Dark: deepen the blue-black surface hierarchy, improve card and navigation
  separation, preserve accessible green verified dots, and moderate neon
  highlights.
- Text: `"System Trust"`, `"Firmware"`, `"Boot image"`, `"Owner key"`,
  `"Verified"`, `"Details"`.
- Additional invariants: preserve left navigation, three connected status
  cards, icons, verified dots, and details pane; no invented measurements,
  shield, or padlock.

### Wallpaper theme variants

Shared invariants: preserve 16:9 framing, each composition's calm UI space and
major geometry, and its analog or painterly texture; no text, logo, watermark,
people, product, or UI.

#### Aurora ridge

- Light: transform pre-dawn into luminous high-altitude dawn with a pale
  cyan-to-lavender sky, softly sunlit snow, warm blush terrain, and a restrained
  magenta-gold halo behind dark light-theme UI.
- Dark: use a navy-black pre-dawn sky, controlled violet terrain, cool cyan snow
  edges, and a restrained magenta-cyan halo with no clipped neon.
- Additional invariants: preserve the panorama, mountain silhouette, low
  horizon, halo placement, and calm upper-left and upper-center; no buildings
  or flags.

#### Owner rings

- Light: use pearlescent pale cyan, lavender, soft blue, warm off-white, and
  restrained magenta inside the painted-glass waves, with enough cool-gray
  depth to retain ring separation.
- Dark: use midnight navy and indigo around controlled cyan and lavender rings,
  restrained magenta at the owner-held core, and tiny acid-green accents.
- Additional invariants: preserve the primary ring slightly right of center,
  nested geometry, tactile texture, and low-detail left side; no literal eye or
  portal.

#### Living root

- Light: use a pale blue-white paper-grain field with deeper cyan circuit-roots,
  violet and magenta petals, emerald-to-acid-green edges, and a warm restrained
  core.
- Dark: use a subtly textured blue-black field; clarify cyan roots, violet and
  magenta petals, emerald edge light, and the warm core without clipping.
- Additional invariants: preserve the bloom low and right of center, branching
  river/root geometry, painterly motion, calm upper third, and left-side
  negative space; no hardware or insects.

#### Nocturne bands

- Light: recast the scene as bright overcast abstract architecture with pale
  mineral-gray and cool blue space, charcoal-to-indigo bands, and sparse cyan,
  magenta, violet, and acid-green pigment pulses.
- Dark: use near-black and deep bottle-green space, blue-black bands with
  readable edges, and sparse cyan, ultraviolet, hot-pink, and ember pulses.
- Additional invariants: preserve sweeping stacked bands from lower-left to
  upper-right, depth, quiet central and top areas, and the concealed bloom-like
  pulse; no recognizable building, faces, or skulls.
