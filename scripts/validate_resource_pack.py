#!/usr/bin/env python3
"""Validate the source pack or a built mcpack, including generated assets."""
import argparse
import json
import zipfile
from pathlib import Path
from generate_pack_animations import definitions, rendered

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "resource-pack"


def read_json(data):
    return json.loads("\n".join(
        line for line in data.decode("utf-8-sig").splitlines()
        if not line.lstrip().startswith("//")
    ))


def validate_files(files, version=None):
    required = {
        "manifest.json", "pack_icon.png", "README.md", "THIRD_PARTY_NOTICES.md",
        "animations/cooldown.animation.json", "animations/weapon_swing.animation.json", "animations/recovery.animation.json", "entity/player.entity.json",
        "animation_controllers/player.animation_controllers.json",
        "attachables/misc/mace.json", "models/entity/item_first_person.json",
        "render_controllers/weapons.render_controllers.json",
    }
    if missing := required - files.keys():
        raise ValueError(f"Missing pack files: {sorted(missing)}")
    docs = {name: read_json(data) for name, data in files.items() if name.endswith(".json")}
    generated = docs["animations/cooldown.animation.json"]
    if generated != definitions() or files["animations/cooldown.animation.json"].decode().replace("\r\n", "\n") != rendered():
        raise ValueError("Generated cooldown animations are stale")
    manifest = docs["manifest.json"]
    if version:
        numeric = [int(part) for part in version.split("-", 1)[0].split(".")]
        if manifest["header"]["version"] != numeric or any(
            module["version"] != numeric for module in manifest["modules"]
        ):
            raise ValueError("Resource pack version mismatch")
    registries = {key: {} for key in ("animations", "animation_controllers", "render_controllers")}
    geometries = {}
    identifiers = set()
    for name, doc in docs.items():
        for group, entries in registries.items():
            for key, value in doc.get(group, {}).items():
                if key in entries:
                    raise ValueError(f"Duplicate {group} definition: {key}")
                entries[key] = value
        for geo in doc.get("minecraft:geometry", []):
            key = geo["description"]["identifier"]
            if key in geometries:
                raise ValueError(f"Duplicate geometry: {key}")
            geometries[key] = {bone["name"] for bone in geo["bones"]}
        if "minecraft:attachable" in doc:
            desc = doc["minecraft:attachable"]["description"]
            key = desc["identifier"]
            if key in identifiers or key.endswith(("_pickaxe", "_hoe", "_shovel")):
                raise ValueError(f"Duplicate or excluded attachable: {key}")
            identifiers.add(key)
            for geo in desc.get("geometry", {}).values():
                if geo not in geometries and not any(
                    geo == g["description"]["identifier"]
                    for d in docs.values() for g in d.get("minecraft:geometry", [])
                ):
                    raise ValueError(f"{name}: missing geometry {geo}")
    for name, doc in docs.items():
        if "minecraft:attachable" not in doc:
            continue
        desc = doc["minecraft:attachable"]["description"]
        bones = set().union(*(geometries[g] for g in desc.get("geometry", {}).values()))
        for animation in desc.get("animations", {}).values():
            if animation in registries["animations"]:
                unknown = registries["animations"][animation].get("bones", {}).keys() - bones
                if unknown:
                    raise ValueError(f"{name}: missing bones {sorted(unknown)}")
            elif animation not in {"animation.bow.wield", "animation.bow.wield_first_person_pull"}:
                raise ValueError(f"{name}: missing animation {animation}")
        for controller in desc["render_controllers"]:
            for key in ([controller] if isinstance(controller, str) else controller):
                if key not in registries["render_controllers"]:
                    raise ValueError(f"{name}: missing render controller {key}")
    for key, animation in registries["animations"].items():
        if key.startswith("animation.player.") and not ("timeline" in animation and not animation.get("bones")) and set(animation.get("bones", {})) != {"rightArm"}:
            raise ValueError(f"{key}: unexpected player bone")
    desc = docs["entity/player.entity.json"]["minecraft:client_entity"]["description"]
    controller = registries["animation_controllers"]["controller.animation.player.first_person_attack"]
    for state in controller["states"].values():
        for entry in state.get("animations", []):
            for alias in ([entry] if isinstance(entry, str) else entry):
                target = desc["animations"].get(alias)
                if not target:
                    raise ValueError(f"Missing player animation alias {alias}")
                if alias.startswith("attack_rotation_custom_") and target not in registries["animations"]:
                    raise ValueError(f"Missing custom player animation {target}")


def validate_archive(data, version):
    import io
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = [n for n in archive.namelist() if not n.endswith("/")]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive entries")
        files = {n: archive.read(n) for n in names}
    validate_files(files, version)
    if files.get("LICENSE") != (ROOT / "LICENSE").read_bytes():
        raise ValueError("Resource pack project license mismatch")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--version")
    args = parser.parse_args()
    if args.archive:
        if not args.version:
            parser.error("--archive requires --version")
        validate_archive(args.archive.read_bytes(), args.version)
    else:
        validate_files({p.relative_to(PACK).as_posix(): p.read_bytes() for p in PACK.rglob("*") if p.is_file()})
    print("Resource pack validation passed")


if __name__ == "__main__":
    main()
