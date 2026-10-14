#!/usr/bin/env python3
"""Build an isolated shield stencil experiment from the known candidate 28."""
import io
import json
from pathlib import Path
import uuid
import zipfile

root = Path(__file__).resolve().parents[2] / "build/bedrock-lab"
source = root / "variants/compact-armor-color/GeyserCooldownAnimation-1.3.15-vv-lab.28.jar"
output = root / "variants/shield-stencil-30"
if output.exists():
    raise SystemExit("Refusing to overwrite candidate 30")
with zipfile.ZipFile(source) as archive:
    entries = {name: archive.read(name) for name in archive.namelist()}
with zipfile.ZipFile(io.BytesIO(entries["geyser-cooldown-animation.mcpack"])) as archive:
    pack = {name: archive.read(name) for name in archive.namelist()}

controller_path = "render_controllers/vv_held_items.render_controllers.json"
controllers = json.loads(pack[controller_path])
new_name = "controller.render.vv_shield_occlusion_mask"
assert new_name not in controllers["render_controllers"]
controllers["render_controllers"][new_name] = {
    "geometry": "Geometry.default",
    "materials": [{"*": "Material.vv_forward_mask"}],
    "textures": ["Texture.default"],
}
pack[controller_path] = json.dumps(controllers, separators=(",", ":")).encode()

shield_path = "attachables/vv_shield.entity.json"
shield = json.loads(pack[shield_path])
description = shield["minecraft:attachable"]["description"]
description["materials"]["vv_forward_mask"] = "vv_forward_mask"
before = description["render_controllers"]
assert len(before) == 2 and "controller.render.vv_item_clean_shield" in before[-1]
before.insert(1, {new_name: "!c.is_first_person"})
pack[shield_path] = json.dumps(shield, separators=(",", ":")).encode()

manifest = json.loads(pack["manifest.json"])
manifest["header"]["uuid"] = str(uuid.uuid4())
manifest["header"]["name"] = "Glowing LAB shield stencil 30"
for module in manifest["modules"]:
    module["uuid"] = str(uuid.uuid4())
pack["manifest.json"] = json.dumps(manifest, separators=(",", ":")).encode()

output.mkdir(parents=True)
with zipfile.ZipFile(output / "shield-stencil-30.mcpack", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name, data in sorted(pack.items()):
        z.writestr(name, data)

entries["geyser-cooldown-animation.mcpack"] = (output / "shield-stencil-30.mcpack").read_bytes()
original = b"version: 1.3.15-vv-lab.28"
assert entries["extension.yml"].count(original) == 1
entries["extension.yml"] = entries["extension.yml"].replace(original, b"version: 1.3.15-vv-lab.30")
jar = output / "GeyserCooldownAnimation-1.3.15-vv-lab.30.jar"
with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name, data in sorted(entries.items()):
        z.writestr(name, data)
(output / "changes.json").write_text(json.dumps({
    "baseline": "candidate 28",
    "purpose": "test if the third-person shield stencil can suppress body outline leakage",
    "changed_files": [controller_path, shield_path, "manifest.json"],
    "not_yet_validated_in_client": True,
    "production_modified": False,
}, indent=2) + "\n")
print(jar)
