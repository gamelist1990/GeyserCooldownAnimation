# Candidate 50 movement and occlusion review

Date: 2026-10-13. Actual Bedrock 1.26.52.3 client, Vibrant Visuals,
local isolated lab. Production was not changed.

Pack SHA-256: `4310f2152a1c08b4e9315c1debd88b5554c85112f3eac8f9f6f3bcc65cddd14b`.

## Repeatable coverage

Plan: `experiments/bedrock-lab/candidate50-rapid-cases.json`.
Evidence: `build/bedrock-lab/runs/candidate50-rapid-v1`.
13 recordings at 30 FPS, 1280 pixels wide. Each uses 40 actions with direction
and view changes every 0.35 seconds, five repetitions of the same eight actions.
Bare, full iron, and Elytra plus iron helmet/leggings/boots are each tested in
open view, behind a one-block wall, behind a four-block wall, and behind a cow.
A final diamond armor case has empty hands. Other cases hold sword and shield.

The Java fixture sends actual 20 Hz movement and input packets. Jump height uses
an explicit flat-floor trajectory (initial velocity 0.42, gravity 0.08, drag 0.98),
not the full Minecraft client collision engine. Horizontal travel is bounded
at 0.8 blocks. This tests actual renderer animation/interpolation; it does not
certify gameplay physics or flight. This run's visible skin is Steve despite
the fixed-skin application log event. Do not claim a pinned synthetic skin from
that event alone. Slim/persona/custom outer layers need separate runs.

## Findings

- Open view: sampled frames follow head pitch/yaw, running legs, jumps and
  crouches. No large filled glow surface was visible in reviewed frames.
- Full wall, bare player: leg contours are faint or partly absent at several
  angles/motion phases. Reproduce with `bare_full_wall_rapid` (for example the
  1–2 second and 4–5 second samples). This is a remaining defect.
- Full wall, iron armor: nested body and armor outlines are visible, especially
  on head and legs. These are not a single outer silhouette. Reproduce with
  `iron_full_wall_rapid`. This is a remaining quality issue.
- Player contours show through held shields as previously requested; held items
  themselves are not outlined. Do not mistake these lines for a filled mask.

All-frame pixel metrics are triage aids. White armor highlights and residual cow
particles are not automatically glow defects. Sample sheets and peak frames
must be visually inspected; no automatic PASS is assigned.

## Glow-off controls and conclusion

Three additional identical movement cases with glowing disabled cover iron,
Elytra plus iron, and empty-handed diamond armor. Evidence is under
`build/bedrock-lab/runs/candidate50-rapid-controls-v1`.
The white rectangular armor reflection is also visible with glow disabled
(e.g. Elytra control at 7.97 seconds), so this observation is not evidence of
mask fill. Across the reviewed open-view and cow-overlap samples, no large
solid glow fill was observed. Elytra remains normally rendered without its own
outline. The unresolved wall leg gaps and nested armor contours prevent a
clean visual quality pass. No runtime pack edits or production changes were
made during these tests.

Total main run: 13 videos, 5,494 decoded frames. Three additional control videos
are reviewed separately. This review uses sampled motion frames and peak-color
frames after measuring every recorded frame; it is not a claim that every
frame was individually inspected or that all possible bugs were excluded.
