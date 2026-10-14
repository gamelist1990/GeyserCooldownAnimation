#!/usr/bin/env python3
"""Prototype 14: isolate the third-person VV stencil bit, no geometry changes.

Item overlap suggests another draw may alter the stencil, but that cause is
unconfirmed. Change only VV material stencil ref/read/write masks to bit 128.
The classic first-person material definitions keep bit 32.
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
    material = json.loads(files["materials/entity.material"])
    changes = []
    for name, definition in material["materials"].items():
        if not name.startswith("vv_") or not isinstance(definition, dict):
            continue
        keys = []
        for key in ("stencilRef", "stencilReadMask", "stencilWriteMask"):
            if definition.get(key) == 32:
                definition[key] = 128
                keys.append(key)
        if keys:
            changes.append((name, keys))
    if len(changes) != 5:
        raise ValueError(f"Expected 5 third-person VV stencil materials, found {len(changes)}")
    files["materials/entity.material"] = encoded(material)
    manifest = json.loads(files["manifest.json"])
    manifest["header"].update(name="Cooldown + Glowing VV STENCIL ISOLATION PROTOTYPE 14",
        description="Only VV stencil ref/read/write bit changes; rendering assets remain prototype 13",
        uuid=str(uuid.uuid4()))
    for module in manifest["modules"]:
        module["uuid"] = str(uuid.uuid4())
    files["manifest.json"] = encoded(manifest)
    changed = {name for name in original if original[name] != files[name]}
    if changed != {"manifest.json", "materials/entity.material"}:
        raise ValueError(f"Unexpected changes: {changed}")
    old = json.loads(original["materials/entity.material"])
    for name, definition in old["materials"].items():
        if not name.startswith("vv_") and material["materials"][name] != definition:
            raise ValueError(f"Classic material changed: {name}")
    output.mkdir(parents=True, exist_ok=True)
    pack = output / "GeyserCooldownAnimation-VV-stencil-isolation-prototype-14.mcpack"
    with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, content in sorted(files.items()):
            z.writestr(name, content)
    jar = output / "GeyserCooldownAnimation-1.3.15-vv-prototype.14.jar"
    with zipfile.ZipFile(jar_source) as source, zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for member in source.infolist():
            content = source.read(member)
            if member.filename == "geyser-cooldown-animation.mcpack":
                content = pack.read_bytes()
            elif member.filename == "extension.yml":
                content = content.replace(b"version: 1.3.15", b"version: 1.3.15-vv-prototype.14")
            z.writestr(member, content)
    print(f"Prototype pack: {pack} ({pack.stat().st_size} bytes)")
    print(f"Prototype JAR: {jar}")
    print("Changed VV stencil materials:", [name for name, _ in changes])


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pack-source", type=Path, required=True)
    p.add_argument("--extension-source", type=Path, required=True)
    p.add_argument("--output", type=Path, default=ROOT / "build/vv-outline-prototype")
    args = p.parse_args()
    build(args.pack_source, args.extension_source, args.output)
