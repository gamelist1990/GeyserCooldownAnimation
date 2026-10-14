#!/usr/bin/env python3
"""Candidate 36: dynamic RGB444 armor outline colors driven by Bedrock entity properties.

No extra hooks or packets: q.property(glow:r/g/b) already mirrors Java team colors.
The vanilla team palette only contains channel levels 0, 85, 170, and 255.
"""
import io
import json
from pathlib import Path
import uuid
import zipfile
from PIL import Image

root = Path(__file__).resolve().parents[2] / "build/bedrock-lab"
source = next((root / "variants/compact-armor-color").glob("GeyserCooldownAnimation-*.jar"))
dest = root / "variants/armor-dynamic-palette36"
if dest.exists():
    raise SystemExit("Candidate36 already exists; refusing overwrite.")

with zipfile.ZipFile(source) as z:
    entries = {n: z.read(n) for n in z.namelist()}
with zipfile.ZipFile(io.BytesIO(entries["geyser-cooldown-animation.mcpack"])) as z:
    pack = {n: z.read(n) for n in z.namelist()}

counts = {"1": 0, "2": 0}
for suffix in ("1", "2"):
    original_name = f"textures/entity/vv_native_coverage_{suffix}.png"
    original_image = Image.open(io.BytesIO(pack[original_name])).convert("RGBA")
    alpha = original_image.getchannel("A")
    for index in range(64):
        color = (((index // 16) % 4) * 85,
                 ((index // 4) % 4) * 85,
                 (index % 4) * 85)
        image = Image.new("RGBA", original_image.size, (*color, 0))
        image.putalpha(alpha)
        stream = io.BytesIO()
        image.save(stream, format="PNG", optimize=True)
        name = f"textures/entity/vv_glow_palette_{suffix}_{index:02d}.png"
        assert name not in pack
        pack[name] = stream.getvalue()
        counts[suffix] += 1

tex_count = 0
for name in list(pack):
    if not name.startswith("attachables/") or not name.endswith(".json"):
        continue
    try:
        doc = json.loads(pack[name])
    except ValueError:
        continue
    desc = doc.get("minecraft:attachable", {}).get("description", {})
    mapping = desc.get("textures", {})
    coverage = mapping.get("vv_native_coverage")
    if coverage not in ("textures/entity/vv_native_coverage_1",
                        "textures/entity/vv_native_coverage_2"):
        continue
    suffix = coverage[-1]
    for index in range(64):
        key = f"vv_glow_palette_{index:02d}"
        assert key not in mapping
        mapping[key] = f"textures/entity/vv_glow_palette_{suffix}_{index:02d}"
    pack[name] = json.dumps(doc, separators=(",", ":")).encode()
    tex_count += 1
assert tex_count >= 20, f"Insufficient armor attachments: {tex_count}"

channel = lambda c: f"math.clamp(math.floor(q.property('glow:{c}') * 3.0 + 0.5), 0.0, 3.0)"
index_expression = f"({channel('r')} * 16.0 + {channel('g')} * 4.0 + {channel('b')})"
for name in ("render_controllers/vv_native_armor.render_controllers.json",
             "render_controllers/vv_bound_helmet.render_controllers.json"):
    doc = json.loads(pack[name])
    for key, controller in doc["render_controllers"].items():
        if not key.endswith("_outline_color"):
            continue
        controller["arrays"] = {
            "textures": {"Array.vv_armor_palette": [
                f"Texture.vv_glow_palette_{index:02d}" for index in range(64)
            ]}
        }
        controller["textures"] = [f"Array.vv_armor_palette[{index_expression}]"]
    pack[name] = json.dumps(doc, separators=(",", ":")).encode()

manifest = json.loads(pack["manifest.json"])
manifest["header"]["uuid"] = str(uuid.uuid4())
manifest["header"]["name"] = "Glowing LAB dynamic armor palette 36"
for module in manifest["modules"]:
    module["uuid"] = str(uuid.uuid4())
pack["manifest.json"] = json.dumps(manifest, separators=(",", ":")).encode()

dest.mkdir(parents=True)
mcpack = dest / "armor-dynamic-palette36.mcpack"
with zipfile.ZipFile(mcpack, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name, contents in sorted(pack.items()):
        z.writestr(name, contents)
entries["geyser-cooldown-animation.mcpack"] = mcpack.read_bytes()
old = b"version: 1.3.15-vv-lab.28"
assert entries["extension.yml"].count(old) == 1
entries["extension.yml"] = entries["extension.yml"].replace(old, b"version: 1.3.15-vv-lab.36")
jar = dest / "GeyserCooldownAnimation-1.3.15-vv-lab.36.jar"
with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name, contents in sorted(entries.items()):
        z.writestr(name, contents)
with zipfile.ZipFile(jar) as z:
    assert z.testzip() is None
    with zipfile.ZipFile(io.BytesIO(z.read("geyser-cooldown-animation.mcpack"))) as res:
        assert res.testzip() is None

(dest / "changes.json").write_text(json.dumps({
    "base": "candidate28",
    "intent": "Match armor outline to mirrored Java team RGB",
    "channel_quantization": [0,85,170,255],
    "texture_count": counts,
    "modified_attachables": tex_count,
    "selector": index_expression,
    "no_item_outline_changes": True,
    "no_extra_packets": True,
    "production_modified": False,
    "visual_status": "untested"
}, indent=2) + "\n")
print("GENERATED", jar, "attachment_count", tex_count, "size", jar.stat().st_size)
