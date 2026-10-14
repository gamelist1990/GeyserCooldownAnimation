#!/usr/bin/env python3
"""Prototype 13: render equipment masks/outlines in the actual armor attachable.

The body/skin pipeline remains from prototype 12. Equipment follows its native
offset animation instead of a separate approximated player-side armor rig.
Client validation is still required for inherited geometry and pass ordering.
"""
import argparse
import copy
import io
import json
from pathlib import Path
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SLOTS = ("helmet", "chestplate", "leggings", "boots")


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def build(pack_source, jar_source, output):
    with zipfile.ZipFile(pack_source) as z:
        files = {name: z.read(name) for name in z.namelist()}
    before = files.copy()
    player = json.loads(files["entity/player.entity.json"])
    desc = player["minecraft:client_entity"]["description"]
    for entry in desc["render_controllers"]:
        if not isinstance(entry, dict):
            continue
        for name in entry:
            if name.startswith("controller.render.vv_armor_mask_") or (
                    name.startswith("controller.render.outline_") and any(f"_{slot}_" in name for slot in SLOTS)):
                entry[name] = "0.0"
    files["entity/player.entity.json"] = encoded(player)
    asset_dir = ROOT / "experiments/vv-native-armor"
    for layer in (1, 2):
        files[f"textures/entity/vv_native_coverage_{layer}.png"] = (asset_dir / f"coverage_{layer}.png").read_bytes()
    files["licenses/Mojang-bedrock-samples-LICENSE.md"] = (asset_dir / "MOJANG-LICENSE.md").read_bytes()
    files["licenses/vv-native-armor-sources.json"] = (asset_dir / "sources.json").read_bytes()
    # Legacy inherited geometry keeps the exact native bones/cubes/UV/reset
    # rules of each equipment slot. Only its outer expansion is increased.
    overrides = {
        "helmet": [("head", 1.3), ("hat", 1.8)],
        "chestplate": [("body", 1.31), ("leftArm", 1.3), ("rightArm", 1.3)],
        "leggings": [("body", 0.8), ("leftLeg", 0.79), ("rightLeg", 0.79)],
        "boots": [("leftLeg", 1.3), ("rightLeg", 1.3)]}
    geometry = {"format_version": "1.8.0"}
    for slot in SLOTS:
        geometry[f"geometry.vv_native_outer_{slot}:geometry.player.armor.{slot}"] = {
            "bones": [{"name": name, "inflate": amount} for name, amount in overrides[slot]]}
    files["models/entity/vv_native_armor_outer.geo.json"] = encoded(geometry)
    armor_controllers = json.loads(files["render_controllers/armor/armor.render_controllers.json"])["render_controllers"]
    armor = armor_controllers.get("controller.render.gca_glowing_armor") or armor_controllers["controller.render.armor"]
    visible = copy.deepcopy(armor)
    visible["materials"] = [{"*": "variable.is_enchanted ? Material.enchanted : Material.default"}]
    visible["rebuild_animation_matrices"] = True
    mask = {"geometry": "Geometry.default", "materials": [{"*": "Material.vv_forward_mask"}],
            "textures": ["Texture.vv_native_coverage"], "rebuild_animation_matrices": True}
    controllers = {"controller.render.vv_native_armor_visible": visible,
                   "controller.render.vv_native_armor_mask": mask}
    for mode, material in [("color", "vv_legacy_outline"), ("black", "vv_legacy_no_esp")]:
        outer = {"geometry": "Geometry.vv_native_outer", "materials": [{"*": f"Material.{material}"}],
            "textures": ["Texture.vv_native_coverage"], "rebuild_animation_matrices": True,
            "ignore_lighting": True}
        color = {channel: (f"q.property('glow:{channel}')" if mode == "color" else 0.0)
                 for channel in ("r", "g", "b")}
        color["a"] = "q.property('glow:a')" if mode == "color" else 1.0
        for key in ("overlay_color", "is_hurt_color", "on_fire_color"):
            outer[key] = copy.deepcopy(color)
        controllers[f"controller.render.vv_native_armor_outline_{mode}"] = outer
    # The visible normal armor has already written scene depth. Restore its
    # normal colors after the white outer pass, using ordinary occlusion.
    front = copy.deepcopy(visible)
    front["materials"] = [{"*": "Material.vv_legacy_skin_front"}]
    controllers["controller.render.vv_native_armor_front"] = front
    files["render_controllers/vv_native_armor.render_controllers.json"] = encoded(
        {"format_version": "1.8.0", "render_controllers": controllers})
    modified = []
    guard = "!c.is_first_person && q.property('glow:color') > 0 && q.property('glow:a') > 0"
    for path in list(files):
        if not path.startswith("attachables/") or not path.endswith(".player.json"):
            continue
        doc = json.loads(files[path])
        attachable = doc.get("minecraft:attachable")
        if not attachable:
            continue
        d = attachable["description"]
        slot = next((slot for slot in SLOTS if d.get("geometry", {}).get("default") == f"geometry.player.armor.{slot}"), None)
        if not slot:
            continue
        original_controllers = copy.deepcopy(d["render_controllers"])
        d["materials"].update(vv_forward_mask="vv_forward_mask", vv_legacy_outline="vv_legacy_outline",
            vv_legacy_no_esp="vv_legacy_no_esp", vv_legacy_skin_front="vv_legacy_skin_front")
        d["textures"]["vv_native_coverage"] = f"textures/entity/vv_native_coverage_{2 if slot == 'leggings' else 1}"
        d["geometry"]["vv_native_outer"] = f"geometry.vv_native_outer_{slot}"
        d["render_controllers"] = [
            {name: "c.is_first_person"} for name in original_controllers]
        d["render_controllers"] += [
            {"controller.render.vv_native_armor_visible": "!c.is_first_person"},
            {"controller.render.vv_native_armor_mask": guard},
            {"controller.render.vv_native_armor_outline_color": f"({guard}) && q.property('glow:color') == 2"},
            {"controller.render.vv_native_armor_outline_black": f"({guard}) && q.property('glow:color') == 1"},
            {"controller.render.vv_native_armor_front": guard}]
        files[path] = encoded(doc)
        modified.append(path)
    if len(modified) != 29:
        raise ValueError(f"Expected 29 equipment attachables, found {len(modified)}")
    # Keep the actual native offset/parent setup/item selection intact.
    for path in modified:
        old = json.loads(before[path])["minecraft:attachable"]["description"]
        new = json.loads(files[path])["minecraft:attachable"]["description"]
        for key in ("identifier", "item", "scripts", "animations"):
            if old.get(key) != new.get(key):
                raise ValueError(f"Native armor behavior changed: {path}: {key}")
    for path in before:
        if path.startswith(("animations/", "animation_controllers/", "models/", "textures/")):
            if files[path] != before[path]:
                raise ValueError(f"Existing body/asset changed: {path}")
        if path.startswith("render_controllers/") and files[path] != before[path]:
            raise ValueError(f"Existing controller changed: {path}")
    manifest = json.loads(files["manifest.json"])
    manifest["header"].update(name="Cooldown + Glowing VV NATIVE ARMOR PROTOTYPE 13",
        description="Experimental equipment-local masks and outlines; body remains prototype 12",
        uuid=str(uuid.uuid4()))
    for module in manifest["modules"]:
        module["uuid"] = str(uuid.uuid4())
    files["manifest.json"] = encoded(manifest)
    output.mkdir(parents=True, exist_ok=True)
    pack = output / "GeyserCooldownAnimation-VV-native-armor-prototype-13.mcpack"
    with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, content in sorted(files.items()):
            z.writestr(name, content)
    jar = output / "GeyserCooldownAnimation-1.3.15-vv-prototype.13.jar"
    with zipfile.ZipFile(jar_source) as original, zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for member in original.infolist():
            content = original.read(member)
            if member.filename == "geyser-cooldown-animation.mcpack":
                content = pack.read_bytes()
            elif member.filename == "extension.yml":
                content = content.replace(b"version: 1.3.15", b"version: 1.3.15-vv-prototype.13")
            z.writestr(member, content)
    print(f"Prototype pack: {pack} ({pack.stat().st_size} bytes)")
    print(f"Prototype JAR: {jar}")
    print(f"Native equipment attachables: {len(modified)}; body/first-person/offset animations preserved")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pack-source", type=Path, required=True)
    p.add_argument("--extension-source", type=Path, required=True)
    p.add_argument("--output", type=Path, default=ROOT / "build/vv-outline-prototype")
    args = p.parse_args()
    build(args.pack_source, args.extension_source, args.output)
