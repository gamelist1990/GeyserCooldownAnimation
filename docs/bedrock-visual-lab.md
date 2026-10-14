# Bedrock visual lab

## Actual client run, 2026-10-13

BedrockOnLinux 2.2.9 launched installed Windows Bedrock 1.26.52.3 on the
physical X11 display with the AMD Radeon Vega GPU. The in-game Video settings
confirmed Vibrant Visuals and third-person front view. FOV was reduced from
110 to 69 for capture. No production pack or server configuration was changed.

The separate Paper/Geyser lab uses Java localhost port 25572, RCON localhost
port 25573, and Bedrock LAN interface port 19142. NetherNet cannot bind to
loopback for working local clients. HAProxy protocol must be disabled in the
lab, although it is enabled in production. Only the test player's existing
Bedrock whitelist identity is copied. A normal `whitelist add` can create the
wrong offline Java UUID; use the existing Floodgate UUID or `fwhitelist`.

The client joined after copying the correct Bedrock whitelist identity.
The first completed run recorded 18 cases for prototype 17: bare player,
A/D, sneak, iron/diamond/chainmail/netherite/leather armor, sword, shield,
trident, mace, axe, block, and pitch changes. Videos, snapshots, pack hash,
commands and input timing are in the ignored directory:

`build/bedrock-lab/runs/prototype17-vv-01/`

**Not a visual pass:** footage of `iron_sneak_sword_shield` reproduces solid
outline-color patches inside the torso and beside held items. The first frame
contains 4024 magenta pixels in the configured ROI. `iron_head_pitch` also
exposes pose/helmet alignment issues. Static screenshots alone miss the bad
frames. The first run used the client's currently selected character; classic
wide/slim skins still need separate runs. Wall/entity occlusion, enchantments,
first person, and repeated long movement runs remain required.

The `double-sided-mask` lab variation (18) repeated all 18 cases. It did not
resolve the torso/item artifact: the iron+sneak+sword+shield video reached
4041 magenta ROI pixels versus 4024 in the baseline, and manual frame review
confirmed the same interior fill. These maxima are not exact cross-run quality
scores because pose timing varies. Variation 19 uses the actual normal player
geometry/controller for the body mask. Its 18-case replay also reproduced the
iron+sneak+sword+shield interior fill; it is not a fix.
The client displayed a different default character after reconnecting for
variation 19. Do not treat color-pixel differences across those skins as a
controlled improvement. A fixed imported classic skin is needed before
quantitative regression thresholds can be accepted.
Variation 20 moves the existing third-person held-item material aliases to
the alphablend/forward family, retaining alpha test and the glint sampler.
It leaves the baseline body, armor, item geometry/animations and first-person
branches unchanged. This probes opaque-item/forward-mask interaction; its
client result is pending.

Variation 20's self replay still showed small interior patches. Rain also
started during that replay, so its color counts are not a controlled comparison.
The runner now sets long-lasting clear weather.

A fixed offline Java player fixture, `VisualProbe`, successfully joined the
dedicated local lab using the installed Geyser protocol library. Head yaw/pitch
and sneak inputs are sent at 20 ticks/s. The Bedrock viewer remains in first
person at a fixed position, so its own fallback skin does not change the target
model across pack reconnects. `run_cases.py --actor probe` starts and stops this
fixture, equips only it, records movement/pose cases, and leaves the viewer's
position fixed. The first remote-player replay is pending review.

Later captures showed that the remote fallback skin was not actually pinned.
A fixed username/server UUID alone does not prove a fixed displayed skin.
Earlier remote runs therefore must not be treated as quantitative skin-matched
comparisons. `VisualProbe` now supplies its deterministic offline profile UUID.
`VisualLabProfile` plus `VisualLabSkin` provide a signed public profile property
and replace its bitmap with an original synthetic wide skin in the dedicated
lab. The runner requires a fresh successful skin-application log for each run
when that fixture extension is installed. Its first two verification attempts
failed before recording; no successful skin pin is claimed for those attempts.

## Continuation: armor union and dynamic evidence

Lab variation 21 combines forward held-item materials with player-side armor
union masks. The masks use full native-sized cubes and armor UV alpha coverage,
so sleeves and boots are not represented by shortened, incorrectly scaled UVs.
It was installed only in the isolated lab, with a fresh pack UUID.

Completed actual-client captures:

- `runs/armor-union-probe-vv-01`: 18 fixed-player conditions.
- `runs/armor-union-occlusion-vv-01`: 6 wall/cow occlusion and pose conditions.
- `runs/armor-union-self-vv-01`: 4 self-view movement/sneak/head conditions.

**Variation 21 is not a completed fix.** The fixed player's bare sneak video,
frame 19, visibly contains solid magenta interior torso/leg patches. Its
`analysis/bare_sneak-max-magenta.png` preserves that failing frame. Selected
iron+sword+shield frames avoid the large fill, but this does not establish
correctness during every pose. Helmet/arm coverage, inside contours and held
item intersections still require correction. Self-view color counts are also
confounded by the client's different fallback skin.

Cow cleanup in the first occlusion replay produced death particles and drops.
The fixture now uses an empty death loot table and a longer settling interval;
rerun those conditions before quantitative comparisons. Counts are not pass
criteria. The ROI was widened from the middle third to the middle half to avoid
cropping sideways movement; compare runs using the same analyzer version.

The client can freeze its visible state behind an idle overlay while a remote
player continues moving. The probe runner wakes it with Ctrl before each case.
The lab's Bedrock whitelist uses the original Floodgate UUID; reconnects now
pass it. The lab server was restarted after its previous process disappeared;
the cause of that termination has not been established.

`live_monitor.py` was exercised for 10 seconds at 5 FPS. It streams only the
Minecraft window, flushes frame measurements to `samples.jsonl` while running,
and saves peak color/change frames. That smoke run verified capture plumbing
after the fixture had left; it is not evidence of a successful outline.

Variation 22 reuses the matching mask's body pose matrices for four outline
controllers. Both wide/slim masks have exactly the same 499 bone definitions
(excluding cubes) as their respective outlines. Six conditions were captured
at 30 FPS/1280 pixels. Bare sneak still visibly filled the torso and legs:
`runs/shared-body-pose-probe-vv-01/analysis/bare_sneak-max-magenta.png`.
Its initial glow-off capture also contains spawn/interpolation contamination;
the runner now settles the initial fixture/viewer teleport for three seconds.

Variation 23 is a **diagnostic**, not a release: it enables color write and
paints the normally invisible body mask green. Six conditions were captured.
Green appeared over regions where previous captures had interior fill. This
does not establish the exact GPU stencil execution order, especially because
the fallback skin differed. Variation 24 tests color-preserving Zero/One
blending instead of DisableColorWrite. It remains experimental.

Content logging exposed a separate correctness issue: the globally overridden
`controller.render.armor` required material aliases absent from vanilla armor
stands. The source now uses `controller.render.gca_glowing_armor` with 30 matching
attachable references, so it does not replace the shared vanilla controller.
All 30 source consumers were checked for the required material aliases.
Existing prototype builders accept both the historical and private names.
Production has not been changed by this correction.

The lab server now runs in the separate `glowing-visual-lab` tmux session.
The client was restarted after repeated pack reloads produced registry errors.
The release criteria are in [outline-quality-criteria.md](outline-quality-criteria.md).

## Scripts

- `scripts/bedrock_lab/prepare_server.py`: creates a new isolated lab from
  installed server binaries; requires an existing Bedrock whitelist player.
- `control.py`: controls and captures only the Minecraft X11 window.
- `rcon.py`: accepts only the localhost lab's dedicated RCON port.
- `run_cases.py`: runs equipment/input cases and stores command responses,
  video, screenshots and timing. Visual status remains `review_required`.
- `analyze_video.py`: exports temporal contact sheets and maximum outline-color
  frames. Requires NumPy/Pillow. White-pixel counts also include ordinary armor
  and light; color metrics are evidence for review, not an automatic pass.
- `VisualProbe.java` / `run_probe.py`: fixed offline player fixture, hardcoded to
  localhost Java port 25572. Only the test lab's whitelist is changed.
- `live_monitor.py`: live color/change measurements and peak frames; requires
  the bundled NumPy/Pillow Python and always reports `review_required`.
- `experiments/bedrock-lab/occlusion-cases.json`: repeatable wall/entity scenes
  combined with armor, held items, head rotation and sneak.
- `experiments/bedrock-lab/stress-cases.json`: 60-second A/D/sneak repetitions,
  bare and with iron armor plus sword/shield. Not yet run.
- `build_skin_fixture.py`, `VisualLabProfile.java`, `VisualLabSkin.java`:
  lab-only deterministic skin. Supply a public signed Mojang textures property
  using `--profile-property`; the displayed bitmap is generated locally.
  Never install these test fixtures in production.

Keep credentials, Xauthority, raw game logs and lab configuration out of Git.
The scripts expect DISPLAY/XAUTHORITY to point to the authorized game session.
Use a new output directory for each replay. Verify the in-game graphics mode
and camera before starting input automation.

## Algorithm references inspected

- [Player-Outline](https://github.com/JuanLuci/Player-Outline): classic stencil
  mask plus an expanded/inverted player shell, closely related to the legacy
  approach. Inspection does not establish Vibrant Visuals compatibility.
- [EdgeRender](https://github.com/mcbe-mods/EdgeRender): explicit block-edge
  geometry with always-visible emissive material. This is not an animated
  player silhouette solution.
- [Fluoroscopy](https://github.com/ryanlua/fluoroscopy): block/PBR texture
  outlines, not a drop-in implementation of player outlines.
- [BedrockOnLinux](https://github.com/Wyze3306/BedrockOnLinux): installed
  Windows/GDK client launcher used for the real dynamic capture.

Reference repositories remain in ignored `build/outline-references/`; no
third-party pack is copied into the released pack by this lab workflow.

### Confirmed skin and compact skeleton experiment

The lab now installs `VisualLabProfile` on isolated Paper and `VisualLabSkin`
on isolated Geyser. A public signed Mojang texture property starts the normal
skin pipeline, after which the Geyser event replaces it with an original
synthetic skin. The runner requires a fresh application event before recording.
No lab fixture is installed in production. Fixed username alone was not enough.

Candidate 26 preserves all body/outline cubes and animated transforms while
collapsing identity helper bones, reducing each model from 499 to 44 bones.
It completed six initial cases, two 60-second stress cases, the full 18-case
plan, eight armor-slot/baseline cases and six occlusion cases. Reviewed peak
frames no longer show the earlier large bare-sneak fill. Recordings still need
full visual review, and shield overlap and armor outline color remain concerns.
The white helmet top also appears with glow off in the matching pitch baseline.
Candidate 27 retains this compaction and tests forward held-item rendering.
It is a separate experiment; it has not been accepted or deployed to production.

### GPU frame diagnostics

`analyze_gpu_capture.py` reads RenderDoc's Vulkan XML export and records
pipeline state, per-face stencil references/write masks and bound vertices.
`replay_elytra.cpp` uses RenderDoc's public replay API to export post-vertex
shader positions for 72-index wing draws. Compile against the same version
of headers/library as the capture tool, with `-DRENDERDOC_PLATFORM_LINUX`,
`-rdynamic` and the required `REPLAY_PROGRAM_MARKER()` symbol. The replay
reader opens only the supplied local capture. It does not control the game.

Use a launch-only Vulkan layer from ignored lab GPU tools for capture. No
global layer registration is needed. Take a frame only after the lab scene
and target pose are visible; F12 is the capture key. Keep all capture data
and launcher logs in ignored build paths. Launcher logs may contain account
diagnostics and must not be published.
