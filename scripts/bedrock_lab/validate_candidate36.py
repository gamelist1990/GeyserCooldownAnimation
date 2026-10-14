#!/usr/bin/env python3
"""Summarize repeatable Bedrock candidate36 validation without claiming automatic visual PASS."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,zipfile
root=Path("/home/pexserver/WorkSpace/DevBox/GeyserCooldownAnimation")
lab=root/"build/bedrock-lab"
names={"candidate36-seven-colors-v1":8,"candidate36-nine-other-colors-v1":9,"candidate36-native-regression-v1":16}
reports=[]
pack_hashes=set()
colors=set()
for name,expected in names.items():
    directory=lab/"runs"/name
    log=json.loads((directory/"run.json").read_text())
    assert len(log["cases"])==expected,(name,len(log["cases"]))
    assert log["actor"]=="probe"
    assert log["fixture_skin"]["applied_event_verified"],name
    assert log["visual_status"]=="review_required"
    pack_hashes.add(log["served_pack_sha256"])
    for c in log["cases"]:
        assert c["visual_status"]=="review_required"
        stem=c["name"]
        assert (directory/(stem+".png")).stat().st_size>10000,stem
        assert (directory/(stem+".mp4")).stat().st_size>10000,stem
        color=c["conditions"].get("team_color","light_purple")
        if c["conditions"].get("glow"):colors.add(color)
    reports.append({"run":name,"cases":len(log["cases"]),"plan_sha256":log["plan_sha256"],
                    "fixed_skin_verified":True,"captures_present":True})
assert len(colors)==16,sorted(colors)
assert len(pack_hashes)==1,pack_hashes
dest=lab/"variants/armor-dynamic-palette36"
jar=dest/"GeyserCooldownAnimation-1.3.15-vv-lab.36.jar"
with zipfile.ZipFile(jar) as z:
    assert z.testzip() is None
    pack=z.read("geyser-cooldown-animation.mcpack")
with zipfile.ZipFile(__import__("io").BytesIO(pack)) as z:
    assert z.testzip() is None
report={
    "generated_utc":datetime.now(timezone.utc).isoformat(),
    "candidate":"36",
    "jar_path":str(jar),
    "jar_sha256":hashlib.sha256(jar.read_bytes()).hexdigest(),
    "served_pack_sha256":next(iter(pack_hashes)),
    "runs":reports,
    "captured_test_cases":sum(x["cases"] for x in reports),
    "all_standard_team_colors_recorded":sorted(colors),
    "assessment":{
        "build_and_capture":"pass",
        "visual_on_off":"manual_pass",
        "armor_team_color_matching":"manual_pass_for_16_standard_colors",
        "armor_materials":"iron,diamond,netherite,chainmail,gold,copper,leather,turtle,partial sets visually reviewed",
        "held_sword_shield":"ordinary item rendering retained",
        "elytra":"known magenta fill issue; separate from armor palette, remains unresolved",
        "flicker":"continuous per-frame quantitative review not yet completed",
        "production":"unchanged; no release or deployment"
    }
}
(dest/"validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
doc=root/"docs/outline-quality-criteria.md"
note="""

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
"""
original=doc.read_text()
if "## Candidate 36 — armor color palette (2026-10-13)" not in original:
    doc.write_text(original+note)
print("CAPTURE_VALIDATION_OK",report["captured_test_cases"],"cases",len(colors),"team colors")
print("JAR_SHA256",report["jar_sha256"])
print("REPORT",dest/"validation.json")
