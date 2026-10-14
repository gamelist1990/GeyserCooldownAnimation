# Outline release criteria

## Required appearance

The release must preserve the normal skin, armor and held-item appearance.
Only the outside silhouette should glow. No interior white/team-color fill,
extra inner body contours, missing hands, doubled helmet outlines, or a skin
visible through a solid wall is accepted.

The outline and mask must follow the same head pitch/yaw, body yaw, arms,
legs, sneak transition and movement pose. Switching glow off must restore the
normal appearance immediately. First-person item location, swing and cooldown
must retain the user-confirmed behavior.

## Repeatable review matrix

| Condition | Required evidence |
| --- | --- |
| Bare classic wide/slim | Idle, repeated A/D, sneak, independent head motion |
| Armor | Each slot alone, mixed slots, full set; iron, diamond, chainmail, netherite, leather |
| Held items | Both empty, sword, shield, both, trident, mace, axe, block; overlap from multiple angles |
| Occlusion | Solid wall and another entity; standing, sneak and rotated head |
| Rendering | Normal graphics and Vibrant Visuals, verified in the client |
| First person | Idle/swing/use/switch items, glow on/off, cooldown |
| Rare flicker | At least 60 seconds of repeated movement/sneak with each risky configuration |

Capture at 30 FPS or higher and at least 1280 pixels wide for detailed review.
Keep the entire target model within frame. Record source pack hash, UUID,
client version, graphics mode, camera, fixed target skin and timing. Compare
the same scene and skin; do not compare color counts across changing persona
skins, resolutions, or ROI definitions.

Color counts and peak-frame detection locate potential failures. They cannot
prove a correct silhouette. Review the full motion and the exported failing
frames, including alpha holes and item overlap. Any observed failing frame
keeps the build in experiment status. Missing conditions are `not_tested`.

## Current status

Variation 21 is experimental and fails bare-player sneak. Its 28 recordings
are completed captures, not 28 passed tests. Variation 22 tests reuse of body
pose matrices after the matching body mask. It is not approved for release.
The full release matrix above has not passed.

## Candidate 26 review (2026-10-13)

Candidate 26 compacts only identity-transform, unanimated body helper bones
from 499 to 44. Assertions preserve every cube and every retained transform.
The synthetic wide target skin is confirmed by a fresh Geyser skin-apply event
in each recording; earlier default-skin captures are not controlled comparisons.

Two 60-second movement/sneak recordings contain 1,805 bare and 1,806 armored
frames. Reviewed peak-color frames and sampled contact sheets show no large
interior fill. This is improvement evidence, not full-motion approval.
Armor pitch with glow off reproduces the bright helmet top: it is also present
in the baseline, rather than sufficient evidence of outline fill.

Remaining review includes item occlusion (thin arm contours appear over the
shield), armor color consistency, all occlusion motion, slim/layered skins,
normal graphics and first-person regression. No production deployment or
release is approved by these partial results.

## Candidates 27-30 (2026-10-13)

Candidates 27 and 28 have seven recordings each, but no full visual PASS.
Candidate 28's moving shield test shows purple inner contours over the shield face.
Candidate 29 changed outline depth from Always to LessEqual; its test was interrupted by a lab watchdog stall and it may break through-wall outlines. Not approved.
Candidate 30 builds a shield-specific stencil pass from candidate 28; the JAR passed archive integrity checks, but Bedrock rendering is **not yet tested**.
Use `build/bedrock-lab/armor-shield-ab-plan.json` for glow ON/OFF, shield ON/OFF, wall occlusion, and movement comparisons. Keep production unchanged.
The client had a 39-chunk render distance and near-full 4GB swap. The original client render distance was restored after testing.


## Candidate 36 — armor color palette (2026-10-13)

User's target is Java-style Glowing on the **player and worn armor**, not on
held sword/shield/items. Body contours crossing an ordinary shield are allowed.
Shield occlusion experiments 29–32 were rejected or made irrelevant.

**Root-cause isolation**:
- Candidate 33 disabled only the armor outline controller passes: white rims
  vanished, while the underlying player outline remained.
- Candidate 34 forced armor controller `color` and `overlay_color` to pure
  magenta: the armor edges remained white. Dynamic color property alone is not
  honored by this armor material.
- Candidate 35 changed only the RGB values of armor coverage textures, leaving
  alpha transparency unchanged: armor outline turned magenta on the actual
  Bedrock client. Thus the color comes from the sampled texture.

**Candidate 36** (lab only) uses 64 textures per armor UV family, with channel
values {0,85,170,255}; texture-array selection indexes using existing
`q.property('glow:r/g/b')`. It supports the normal 16 Java team colors with
no additional packets and does not change held items. 29 armor attachables
were updated in the generated pack. Build source:
`scripts/bedrock_lab/build_armor_dynamic_palette36.py`.

Evidence:
- `build/bedrock-lab/runs/candidate36-seven-colors-v1` (7 named team colors +
  one Glow OFF baseline, all captured)
- `build/bedrock-lab/runs/candidate36-nine-other-colors-v1` (remaining 9 named
  colors, all captured)
- `build/bedrock-lab/runs/candidate36-native-regression-v1` (16 worn-equipment,
  wall, motion, item and OFF scenarios, all captured)
- `build/bedrock-lab/variants/armor-dynamic-palette36/validation.json`
  contains the reproducible pack hash and capture checks.

Manual frame review confirms head/shoulder/leg outline hues match the team
color for all 16 tested names, and the armor silhouette disappears when glow
is disabled. Iron, diamond, netherite, leather, copper, gold, chainmail, partial
armor and turtle helmet were inspected. Sword and shield were not recolored.

**Unresolved**: Elytra sometimes renders a large magenta filled wing rather
than a thin outside contour. Candidate36 does not change elytra controllers:
investigate separately before any claim of full native parity. Review dynamic
flicker and slim-skin variants before production release.

Production server/plugins remain unchanged. The dedicated lab currently uses
candidate36 for further testing.
