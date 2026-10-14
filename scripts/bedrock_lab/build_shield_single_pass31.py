#!/usr/bin/env python3
"""Experimental single-pass shield stencil writer, isolated candidate 31."""
import io
import json
from pathlib import Path
import uuid
import zipfile

root = Path(__file__).resolve().parents[2] / "build/bedrock-lab"
src = root / "variants/compact-armor-color/GeyserCooldownAnimation-1.3.15-vv-lab.28.jar"
dst = root / "variants/shield-single-pass-31"
if dst.exists():
    raise SystemExit("Refusing to overwrite existing candidate 31")

with zipfile.ZipFile(src) as z:
    entries = {key: z.read(key) for key in z.namelist()}
with zipfile.ZipFile(io.BytesIO(entries["geyser-cooldown-animation.mcpack"])) as z:
    pack = {key: z.read(key) for key in z.namelist()}

path = "materials/entity.material"
doc = json.loads(pack[path])
materials = doc["materials"]
for source, target in (("vv_item_clean:entity_alphatest", "vv_shield_stencil:entity_alphatest"),
                       ("vv_item_clean_glint:entity_alphatest_glint", "vv_shield_stencil_glint:entity_alphatest_glint")):
    assert target not in materials and source in materials
    materials[target] = {
        "+states": ["EnableStencilTest", "StencilWrite"],
        "stencilRef": 128, "stencilReadMask": 128, "stencilWriteMask": 128,
        "frontFace": {"stencilFunc": "Always", "stencilFailOp": "Keep",
                      "stencilDepthFailOp": "Keep", "stencilPassOp": "Replace"},
        "backFace": {"stencilFunc": "Always", "stencilFailOp": "Keep",
                     "stencilDepthFailOp": "Keep", "stencilPassOp": "Replace"},
    }
pack[path] = json.dumps(doc, separators=(",", ":")).encode()

path = "attachables/vv_shield.entity.json"
shield = json.loads(pack[path])
desc = shield["minecraft:attachable"]["description"]
assert desc["materials"]["vv_item_clean"] == "vv_item_clean"
assert desc["materials"]["vv_item_clean_glint"] == "vv_item_clean_glint"
assert len(desc["render_controllers"]) == 2
desc["materials"]["vv_item_clean"] = "vv_shield_stencil"
desc["materials"]["vv_item_clean_glint"] = "vv_shield_stencil_glint"
pack[path] = json.dumps(shield, separators=(",", ":")).encode()

manifest = json.loads(pack["manifest.json"])
manifest["header"]["uuid"] = str(uuid.uuid4())
manifest["header"]["name"] = "Glowing LAB shield single pass 31"
for mod in manifest["modules"]:
    mod["uuid"] = str(uuid.uuid4())
pack["manifest.json"] = json.dumps(manifest, separators=(",", ":")).encode()

dst.mkdir(parents=True)
packfile = dst / "shield-single-pass-31.mcpack"
with zipfile.ZipFile(packfile, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name, data in sorted(pack.items()):
        z.writestr(name, data)

entries["geyser-cooldown-animation.mcpack"] = packfile.read_bytes()
old = b"version: 1.3.15-vv-lab.28"
assert entries["extension.yml"].count(old) == 1
entries["extension.yml"] = entries["extension.yml"].replace(old, b"version: 1.3.15-vv-lab.31")
jar = dst / "GeyserCooldownAnimation-1.3.15-vv-lab.31.jar"
with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name, data in sorted(entries.items()):
        z.writestr(name, data)
with zipfile.ZipFile(jar) as z:
    assert z.testzip() is None
(dst / "changes.json").write_text(json.dumps({
    "base": "candidate 28", "experiment": "write stencil in original shield render pass",
    "avoids": "candidate 30 additional render controller (rotated shield)",
    "new_materials": ["vv_shield_stencil", "vv_shield_stencil_glint"],
    "pass_count_unchanged": True, "production_modified": False,
    "visual_status": "untested"}, indent=2) + "\n")
print(jar)
