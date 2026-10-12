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
    vanilla_geometries = {"geometry.elytra", *("geometry.player.armor." + slot for slot in ("boots", "chestplate", "helmet", "leggings"))}
    vanilla_animations = {"animation.bow.wield", "animation.bow.wield_first_person_pull", "controller.animation.elytra.default",
                          *("animation.elytra." + state for state in ("default", "gliding", "sleeping", "sneaking", "swimming")),
                          *("animation.armor." + slot + ".offset" for slot in ("boots", "chestplate", "helmet", "leggings"))}
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
            if key in identifiers:
                raise ValueError(f"Duplicate attachable: {key}")
            identifiers.add(key)
            for geo in desc.get("geometry", {}).values():
                if geo not in vanilla_geometries and geo not in geometries and not any(
                    geo == g["description"]["identifier"]
                    for d in docs.values() for g in d.get("minecraft:geometry", [])
                ):
                    raise ValueError(f"{name}: missing geometry {geo}")
    for name, doc in docs.items():
        if "minecraft:attachable" not in doc:
            continue
        desc = doc["minecraft:attachable"]["description"]
        bones = set().union(*(geometries.get(g, set()) for g in desc.get("geometry", {}).values()))
        aliases = desc.get("animations", {})
        for animation in aliases.values():
            if animation in registries["animations"]:
                unknown = registries["animations"][animation].get("bones", {}).keys() - bones
                if unknown:
                    raise ValueError(f"{name}: missing bones {sorted(unknown)}")
            elif animation in registries["animation_controllers"]:
                controller = registries["animation_controllers"][animation]
                for state in controller["states"].values():
                    for entry in state.get("animations", []):
                        for alias in ([entry] if isinstance(entry, str) else entry):
                            if alias not in aliases:
                                raise ValueError(f"{name}: missing controller animation alias {alias}")
                    for transition in state.get("transitions", []):
                        if transition.keys() - controller["states"].keys():
                            raise ValueError(f"{name}: missing controller state")
            elif animation not in vanilla_animations:
                raise ValueError(f"{name}: missing animation {animation}")
        for controller in desc["render_controllers"]:
            for key in ([controller] if isinstance(controller, str) else controller):
                if key not in registries["render_controllers"]:
                    raise ValueError(f"{name}: missing render controller {key}")
        for entry in desc.get("scripts", {}).get("animate", []):
            for alias in ([entry] if isinstance(entry, str) else entry):
                if alias not in aliases:
                    raise ValueError(f"{name}: missing script animation alias {alias}")
    materials = ("wooden", "stone", "copper", "iron", "golden", "diamond", "netherite")
    expected = {f"minecraft:{material}_{kind}" for material in materials for kind in ("pickaxe", "shovel", "spear")}
    expected |= {"minecraft:trident", "minecraft:mace"}
    if missing := expected - identifiers:
        raise ValueError(f"Missing supported attachables: {sorted(missing)}")
    for key, animation in registries["animations"].items():
        if key.startswith("animation.player.") and not ("timeline" in animation and not animation.get("bones")) and set(animation.get("bones", {})) != {"rightArm"}:
            raise ValueError(f"{key}: unexpected player bone")
    desc = docs["entity/player.entity.json"]["minecraft:client_entity"]["description"]
    item_fix = desc.get("animations", {}).get("first_person_item_fix")
    if item_fix is not None and item_fix not in registries["animations"]:
        raise ValueError("Player first-person item-fix alias must resolve in the served pack")
    player_controllers = [registries["animation_controllers"][name] for name in (
        "controller.animation.player.first_person_attack", "controller.animation.geyser_cooldown.recovery")]
    for state in (state for controller in player_controllers for state in controller["states"].values()):
        for entry in state.get("animations", []):
            for alias in ([entry] if isinstance(entry, str) else entry):
                target = desc["animations"].get(alias)
                if not target:
                    raise ValueError(f"Missing player animation alias {alias}")
                if alias.startswith(("attack_rotation_custom_", "gca_recovery_")) and target not in registries["animations"]:
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
