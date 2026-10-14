#!/usr/bin/env python3
"""Lab-only candidate 32: depth-test only shield-side player arm outlines."""
import copy
import io
import json
from pathlib import Path
import uuid
import zipfile

root = Path(__file__).resolve().parents[2] / "build/bedrock-lab"
source = root / "variants/compact-armor-color/GeyserCooldownAnimation-1.3.15-vv-lab.28.jar"
out = root / "variants/shield-arm-depth-32"
if out.exists():
    raise SystemExit("Refusing to overwrite existing candidate 32")

with zipfile.ZipFile(source) as archive:
    jar = {name: archive.read(name) for name in archive.namelist()}
with zipfile.ZipFile(io.BytesIO(jar["geyser-cooldown-animation.mcpack"])) as archive:
    pack = {name: archive.read(name) for name in archive.namelist()}

mat_path = "materials/entity.material"
materials_doc = json.loads(pack[mat_path])
materials = materials_doc["materials"]
source_mat = "vv_legacy_outline:entity_alphablend"
target_mat = "vv_shield_arm_depth:entity_alphablend"
assert target_mat not in materials
materials[target_mat] = copy.deepcopy(materials[source_mat])
assert materials[target_mat]["depthFunc"] == "Always"
materials[target_mat]["depthFunc"] = "LessEqual"
pack[mat_path] = json.dumps(materials_doc, separators=(",", ":")).encode()

player_path = "entity/player.entity.json"
player_doc = json.loads(pack[player_path])
player = player_doc["minecraft:client_entity"]["description"]
assert "vv_shield_arm_depth" not in player["materials"]
player["materials"]["vv_shield_arm_depth"] = "vv_shield_arm_depth"
pack[player_path] = json.dumps(player_doc, separators=(",", ":")).encode()

for shape, controller_path, geo_path, target in [
    ("wide", "render_controllers/wide/outline_wide_player.render_controllers.json",
     "models/entity/wide_player_outline.geo.json", "controller.render.wide_outline_layer_customization"),
    ("slim", "render_controllers/slim/outline_player.render_controllers.json",
     "models/entity/player_outline.geo.json", "controller.render.outline_layer_customization"),
]:
    bones = [bone["name"] for bone in json.loads(pack[geo_path])["minecraft:geometry"][0]["bones"]]
    doc = json.loads(pack[controller_path])
    rc = doc["render_controllers"][target]
    assert len(rc["materials"]) == 1
    for side, slot in (("left", "offhand"), ("right", "mainhand")):
        cond = f"query.is_item_name_any('slot.weapon.{slot}', 'minecraft:shield')"
        expression = f"{cond} ? Material.vv_shield_arm_depth : Material.vv_legacy_outline"
        for bone in bones:
            if bone == f"{side}Arm" or bone.startswith(f"{side}Sleeve"):
                rc["materials"].append({bone: expression})
    pack[controller_path] = json.dumps(doc, separators=(",", ":")).encode()

manifest = json.loads(pack["manifest.json"])
manifest["header"]["name"] = "Glowing LAB shield arm depth 32"
manifest["header"]["uuid"] = str(uuid.uuid4())
for module in manifest["modules"]:
    module["uuid"] = str(uuid.uuid4())
pack["manifest.json"] = json.dumps(manifest, separators=(",", ":")).encode()

out.mkdir(parents=True)
mcpack = out / "shield-arm-depth-32.mcpack"
with zipfile.ZipFile(mcpack, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name, value in sorted(pack.items()):
        archive.writestr(name, value)
jar["geyser-cooldown-animation.mcpack"] = mcpack.read_bytes()
old = b"version: 1.3.15-vv-lab.28"
assert jar["extension.yml"].count(old) == 1
jar["extension.yml"] = jar["extension.yml"].replace(old, b"version: 1.3.15-vv-lab.32")
target_jar = out / "GeyserCooldownAnimation-1.3.15-vv-lab.32.jar"
with zipfile.ZipFile(target_jar, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name, value in sorted(jar.items()):
        archive.writestr(name, value)
with zipfile.ZipFile(target_jar) as archive:
    assert archive.testzip() is None
(out / "changes.json").write_text(json.dumps({
    "base": "candidate 28", "experiment": "LessEqual depth only on outline bones of shield-side arm",
    "preserves": "global Always depth on torso/head/legs and regular shield attachable",
    "intended": "hide thin arm contours behind shield without losing global glow through walls",
    "status": "experimental; needs Bedrock screen and motion review", "production_modified": False
}, indent=2) + "\n")
print(target_jar)
