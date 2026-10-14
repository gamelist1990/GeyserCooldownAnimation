# GeyserGlow visual development continuation — 2026-10-13

## Scope and production safety

Lab: `build/bedrock-lab/server` on localhost Java port 25572.
The production server has not been modified. Candidate 36 is the
last armor-color variant visually validated on a Bedrock client.
Held item silhouettes (sword/shield) are intentionally excluded.

## Baseline candidate 36

- 33 recorded scenarios, including 16 Java team color names and 16
  equipment/occlusion/motion cases. Wide fixture skin was verified.
- Worn armor (iron, diamond, netherite, leather, copper, chainmail,
  gold, partial armor, turtle shell) follows player team color.
- Glow OFF and held sword/shield ordinary appearance reviewed.
- Static validation `scripts/bedrock_lab/validate_palette_and_variants.py`
  confirms 29 patched armor attachables, 128 indexed palette textures
  with their original alpha masks, and both wide (4px arm) and slim
  (3px arm) renderer definitions.
- **Not yet verified**: true Slim client footage and stringent
  per-frame inspection under every animation.

## Elytra experimental variants

The old player Elytra outline render path is separate from the 29 armor
attachables' indexed color texture path. It was rendering oversized
opaque colored wing surfaces, rather than just an outer contour.

- **37:** Added `vv_elytra_mask` geometry with small inflation
  (0.45) and a color/depth-write-disabled Stencil pass before the
  colored wing. The original outer wing remained inflated by 1.2.
  6 actual Bedrock captures, front/side/back/sneak, OFF and armor.
  Opaque fill shrank, but fat magenta triangles remained in side views.
- **38:** From 37, shrank outer inflate to 0.35, inner mask to 0.12,
  body scale to 1.012, and wing Z scale to 1.08. Same 6 cases
  recorded. Result: less intrusive purple, but wing outer contour is
  too faint or incomplete at some viewing angles. Not accepted yet.
- **39:** Balanced values (outer 0.65, mask 0.28, body 1.025, wing
  Z 1.35), JAR integrity check passed. The actual Bedrock comparison
  remains **untested** because Remote Desktop graphical control was
  blocked by a safety check. Do not claim this variant passes.

On the fixed viewport/crop and screenshot color threshold used for
the experimental comparison, magenta region counts were:

| View | Variant 37 | Variant 38 |
| --- | ---: | ---: |
| Front | 6,643 | 3,535 |
| Side | 6,707 | 4,353 |
| Back | 8,082 | 4,948 |
| Sneak | 6,622 | 3,565 |

Those are review aids (include player body silhouette) rather than
an exact measurement of the Elytra alone. Visual inspection is required.

## Animation/video observations

On stationary candidate36 `iron_full.mp4`, a 12fps subsampling
over a 250x300 pixel region counted 1,841–1,964 magenta pixels
(mean 1,909, standard deviation 37, **no empty frames**).
This does not prove freedom from fine flicker, and frame counts can
be affected by camera, animation and sampling.

Reproducible analysis script:
`scripts/bedrock_lab/analyze_stability_no_numpy.py`

## Follow-up: Slim skin

Slim (3px arms) model and fixture both exist. Fixture package:
`build/bedrock-lab/skin-fixture-slim-layered/VisualLabSkin-0.1.0.jar`.
After obtaining permission for GUI interaction and isolating the
running test lab, swap only the lab's existing fixture JAR (back up
first), restart the lab, and rerun the same connected Bedrock client
using `build/bedrock-lab/slim-followup-plan.json`. Verify the log
says `Applied fixed slim lab skin`. Do not infer that static checks
alone constitute a visual pass.

## Decision

**Keep candidate36 as the last Bedrock-verified armor baseline.**
The Elytra experiments 37/38 are partial improvements, 39 unverified,
and none is promoted to production. Continue only when graphical
control becomes available again; avoid unrelated Minecraft processes.

## Resumed from candidate 43

Candidate 43 is the installed lab baseline at handoff. Its six-case rerun
(`candidate43-resumed-six-v1`) still shows detached magenta wing surfaces
in side/back/sneak views; removing matrix rebuilding did not resolve it.

Candidate 44 is a diagnostic using `Geometry.default` for BOTH the native
Elytra mask and colored pass. It deliberately has no enlarged wing. If a
colored wing remains, matching dimensions alone cannot explain the failure.
Only the two controller geometry references and manifest change from 43.
The installed client 1.26.52.3's uncompressed vanilla model/animation archives
were read locally: their wing cuboids and default/sneak animations match
Mojang's sample. They are saved under ignored lab references.

The synthetic fixture now uses a fresh skin ID per application to avoid
reusing a prior client skin bitmap. Actual recorded skin must still be
visually confirmed; a server event alone is not sufficient evidence.

Candidate 44 completed six captures (`candidate44-native-identity-v1`).
Despite identical `Geometry.default` references, detached colored wing
surfaces remain; it is rejected as a release, and retained as diagnostic
evidence. Native texture alpha also matches the sample byte for byte.
Candidate 45 additionally makes the mask use the same palette texture array
as the colored pass to isolate texture/pipeline differences. It retains
zero expansion and is not a usable outline release.

Candidate 45 completed three diagnostic captures (`candidate45-texture-identity-v1`);
the detached wing surface remains. Matching the mask/outline texture did not
eliminate it. Candidate 46 tests a dedicated double-sided Elytra mask with
identical native geometry, retaining zero expansion. This tests whether the
one-sided alpha-tested mask misses the back-facing wing surface. The shared
body/armor mask material is untouched. No result is inferred before capture.

Candidate 46 completed three captures (`candidate46-double-sided-v1`).
Detached native wing color remains even with a dedicated double-sided mask.
Neither diagnostic establishes the renderer's actual stencil execution order.
Next step is an isolated RenderDoc frame capture of the lab game process.
All downloaded GPU tools and their launch-only Vulkan layer remain under
ignored lab directories; production and global Vulkan configuration are untouched.

### Actual GPU evidence from 46

Two RenderDoc 1.46 Vulkan captures contain Glow ON/OFF in the same lab scene.
The native mask and color draws use 72 indices, vertex buffer 3395, offset
28784, stride 28. Mask event 1050 precedes color event 1058 in the same
command buffer, and actual stencil reference/read mask are 128. The dedicated
mask has culling disabled and color writes disabled. These are measured GPU
states, not inferred resource-pack metadata.

The public replay API successfully exports vertex-shader output after adding
the required `REPLAY_PROGRAM_MARKER` symbol to the standalone evidence reader.
Without that marker, RenderDoc treated the reader as a capture application and
crashed; this was corrected in the reader, not in Minecraft.

With identical native geometry, the color pass clip-space X coordinates are
approximately 1.067 times the mask pass coordinates. This matches the native
Elytra body's animation scale and supports repeated matrix application.
Candidate 47 explicitly sets `rebuild_animation_matrices: false` in both
passes, still with zero expansion. Candidate 43 merely omitted the field.
Evidence remains under ignored `build/bedrock-lab/gpu-captures`; reusable
readers are `analyze_gpu_capture.py` and `replay_elytra.cpp`.

Candidate 47 explicitly disabled matrix rebuilding but the three diagnostic
captures still show the detached surface. The flag alone is insufficient.
Candidate 48 moves the constant 1.067 uniform body scale into each wing's
local scale and translation, using private native animations. All rotation
expressions, cubes, UVs, controller states and geometry references are retained.
Because both wing pivots equal the body pivot, uniform scale commutes with
rotation; scaling wing translation and local scale preserves the native pose.
The diagnostic still has zero silhouette expansion to test alignment first.

## User scope change: candidate 50

The user dropped Elytra wing outline support. Preserve normal Elytra rendering
and let the player outline show through the wings. Candidate 50 starts from the
validated player/armor candidate 36, disables both player wing outline render
controllers, limits the legacy wing animation to first person, and gives the
native Elytra a dedicated stencil-neutral third-person render controller.
Native wing geometry, textures and animations remain unchanged. The first-person
material expression is retained from candidate 36. No experiments 37–49 are
required for this scope. The isolated lab runs candidate 50; production remains
unchanged until visual review. Builder: `scripts/bedrock_lab/build_elytra_passthrough50.py`.

Candidate 50 actual VV review: four captures in `build/bedrock-lab/runs/candidate50-passthrough-v1` (front, back, glow off, iron helmet/leggings/boots plus sword/shield during sneak movement). Native gray wings remain visible without a wing glow surface; player/armor contour remains visible through the wings. No detached wing/floor fill was visible in the reviewed final frames. This is a short regression, not exhaustive certification.
