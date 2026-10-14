#!/usr/bin/env python3
"""Prototype 16: explicit holder-head binding for helmet mask and outer shell.

Only helmets change. Normal helmet/first-person rendering and other equipment
remain prototype 15. Actual binding coordinates need a Bedrock client check.
"""
import argparse
import copy
import json
from pathlib import Path
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def build(pack_source, jar_source, output):
    with zipfile.ZipFile(pack_source) as z:
        files = {name: z.read(name) for name in z.namelist()}
    original = files.copy()
    geometries = []
    for kind, expansion in (("mask", 0.0), ("outer", 0.3)):
        geometries.append({"description": {"identifier": f"geometry.vv_bound_helmet_{kind}",
            "texture_width": 64, "texture_height": 32, "visible_bounds_width": 3,
            "visible_bounds_height": 3, "visible_bounds_offset": [0, 1, 0]},
            "bones": [{"name": "vv_bound_helmet_head", "binding": "'head'", "pivot": [0, 24, 0],
                "cubes": [
                    {"origin": [-4, 24, -4], "size": [8, 8, 8], "uv": [0, 0], "inflate": 1.0 + expansion},
                    {"origin": [-4, 24, -4], "size": [8, 8, 8], "uv": [32, 0], "inflate": 0.5 + expansion}]}]})
    files["models/entity/vv_bound_helmet.geo.json"] = encoded(
        {"format_version": "1.16.0", "minecraft:geometry": geometries})
    files["animations/vv_bound_helmet.animation.json"] = encoded({"format_version": "1.8.0",
        "animations": {"animation.vv_bound_helmet.offset": {"loop": True,
            "bones": {"vv_bound_helmet_head": {"position": [
                f"query.get_root_locator_offset('armor_offset.helmet', {axis})" for axis in range(3)]}}}}})
    source = json.loads(files["render_controllers/vv_native_armor.render_controllers.json"])["render_controllers"]
    controllers = {}
    replacement = {}
    for role in ("mask", "outline_color", "outline_black"):
        old = f"controller.render.vv_native_armor_{role}"
        new = f"controller.render.vv_bound_helmet_{role}"
        replacement[old] = new
        controller = copy.deepcopy(source[old])
        controller["geometry"] = "Geometry.vv_bound_mask" if role == "mask" else "Geometry.vv_bound_outer"
        controllers[new] = controller
    files["render_controllers/vv_bound_helmet.render_controllers.json"] = encoded(
        {"format_version": "1.8.0", "render_controllers": controllers})
    count = 0
    for name in list(files):
        if not name.startswith("attachables/") or not name.endswith(".player.json"):
            continue
        doc = json.loads(files[name])
        d = doc.get("minecraft:attachable", {}).get("description", {})
        if d.get("geometry", {}).get("default") != "geometry.player.armor.helmet":
            continue
        d["geometry"].update(vv_bound_mask="geometry.vv_bound_helmet_mask",
                             vv_bound_outer="geometry.vv_bound_helmet_outer")
        d["animations"]["vv_bound_helmet_offset"] = "animation.vv_bound_helmet.offset"
        d["scripts"]["animate"].append({"vv_bound_helmet_offset": "!c.is_first_person"})
        for entry in d["render_controllers"]:
            if isinstance(entry, dict):
                for old in list(entry):
                    if old in replacement:
                        entry[replacement[old]] = entry.pop(old)
        files[name] = encoded(doc)
        count += 1
    if count != 8:
        raise ValueError(f"Expected 8 helmet attachables, found {count}")
    for name in original:
        if files[name] != original[name] and not (name.startswith("attachables/") and "helmet.player.json" in name):
            raise ValueError(f"Unexpected change outside helmets: {name}")
    manifest = json.loads(files["manifest.json"])
    manifest["header"].update(name="Cooldown + Glowing VV BOUND HELMET PROTOTYPE 16",
        description="Explicit holder head binding for helmet mask/outline; other rendering remains prototype 15",
        uuid=str(uuid.uuid4()))
    for module in manifest["modules"]:
        module["uuid"] = str(uuid.uuid4())
    files["manifest.json"] = encoded(manifest)
    output.mkdir(parents=True, exist_ok=True)
    pack = output / "GeyserCooldownAnimation-VV-bound-helmet-prototype-16.mcpack"
    with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, content in sorted(files.items()):
            z.writestr(name, content)
    jar = output / "GeyserCooldownAnimation-1.3.15-vv-prototype.16.jar"
    with zipfile.ZipFile(jar_source) as src, zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for member in src.infolist():
            content = src.read(member)
            if member.filename == "geyser-cooldown-animation.mcpack":
                content = pack.read_bytes()
            elif member.filename == "extension.yml":
                content = content.replace(b"version: 1.3.15", b"version: 1.3.15-vv-prototype.16")
            z.writestr(member, content)
    print(f"Prototype pack: {pack} ({pack.stat().st_size} bytes)")
    print(f"Prototype JAR: {jar}")
    print("Changed 8 helmets; body, chestplate, legs, held items and first-person controllers preserved")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pack-source", type=Path, required=True)
    p.add_argument("--extension-source", type=Path, required=True)
    p.add_argument("--output", type=Path, default=ROOT / "build/vv-outline-prototype")
    args = p.parse_args()
    build(args.pack_source, args.extension_source, args.output)
