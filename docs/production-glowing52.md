# Production promotion of the current Bedrock lab build

The user requested promotion of the installed candidate 52 on 2026-10-15.
`releases/bedrock-verified/GeyserCooldownAnimation-1.3.15-vv-lab.52.jar`
is the exact installed lab artifact, including its embedded resource pack.
Its existing version and pack identity are retained to avoid introducing
unreviewed renderer changes. SHA-256 values are in `deployment.json`.
GeyserJavaGlowing remains 0.2.13, the same version already used in production.
No VisualLabProfile or VisualLabSkin fixture is deployed.

Candidate 52 builds on candidate 50 with covered body parts hidden beneath
armor and the native player geometry used for the body mask. It retains
normal Elytra rendering without a wing outline. Builder history is in
`scripts/bedrock_lab/`; the ordinary Gradle resource pack is the older
baseline and must not be substituted for this promoted artifact.

The user accepted the lab result; this is not an exhaustive visual pass.
The candidate 50 motion review records wall silhouette limitations, and
Slim/persona coverage remains incomplete. Candidate 52's original diagnostic
metadata is retained rather than retroactively claiming automated approval.

Lab runtime data, captures, worlds and credentials now live at
`/home/pexserver/WorkSpace/Bedrocklab`. The old ignored `build/bedrock-lab`
path is a compatibility symlink so existing scripts and historical evidence
paths continue to work. The lab was stopped before relocation and remains
stopped. Do not commit its runtime data or credentials.
