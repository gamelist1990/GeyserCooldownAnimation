#!/usr/bin/env python3
"""Prototype 15: use normal armor matrix handling for the native armor passes.

Only disable forced matrix rebuilding on the five added armor controllers.
Body masks, item/first-person transforms and stencil settings remain unchanged.
Whether this restores inherited head/arm pose requires a Bedrock client check.
"""
import argparse
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
    path = "render_controllers/vv_native_armor.render_controllers.json"
    doc = json.loads(files[path])
    if len(doc["render_controllers"]) != 5:
        raise ValueError("Unexpected native armor controller count")
    for name, controller in doc["render_controllers"].items():
        if not name.startswith("controller.render.vv_native_armor_") or controller.get("rebuild_animation_matrices") is not True:
            raise ValueError(f"Unexpected original controller: {name}")
        controller.pop("rebuild_animation_matrices")
    files[path] = encoded(doc)
    manifest = json.loads(files["manifest.json"])
    manifest["header"].update(name="Cooldown + Glowing VV ARMOR POSE PROTOTYPE 15",
        description="Native armor matrix handling; body and item transforms remain prototype 14",
        uuid=str(uuid.uuid4()))
    for module in manifest["modules"]:
        module["uuid"] = str(uuid.uuid4())
    files["manifest.json"] = encoded(manifest)
    changed = {name for name in original if files[name] != original[name]}
    if changed != {"manifest.json", path}:
        raise ValueError(f"Unexpected changes: {changed}")
    output.mkdir(parents=True, exist_ok=True)
    pack = output / "GeyserCooldownAnimation-VV-armor-pose-prototype-15.mcpack"
    with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, content in sorted(files.items()):
            z.writestr(name, content)
    jar = output / "GeyserCooldownAnimation-1.3.15-vv-prototype.15.jar"
    with zipfile.ZipFile(jar_source) as source, zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for member in source.infolist():
            content = source.read(member)
            if member.filename == "geyser-cooldown-animation.mcpack":
                content = pack.read_bytes()
            elif member.filename == "extension.yml":
                content = content.replace(b"version: 1.3.15", b"version: 1.3.15-vv-prototype.15")
            z.writestr(member, content)
    print(f"Prototype pack: {pack} ({pack.stat().st_size} bytes)")
    print(f"Prototype JAR: {jar}")
    print("Only five native armor matrix rebuild flags removed; all other rendering data preserved")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pack-source", type=Path, required=True)
    p.add_argument("--extension-source", type=Path, required=True)
    p.add_argument("--output", type=Path, default=ROOT / "build/vv-outline-prototype")
    args = p.parse_args()
    build(args.pack_source, args.extension_source, args.output)
