#!/usr/bin/env python3
"""Prototype 17: third-person held item materials do not write/test stencil.

Preserve existing item geometry, animations, scripts and first-person branches.
Include the vanilla shield with its original first-person controller. This is
a material-state isolation experiment, not a client-verified visual fix.
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
    material = json.loads(files["materials/entity.material"])
    for name, parent in [("vv_item_clean", "entity_alphatest"),
                         ("vv_item_clean_glint", "entity_alphatest_glint")]:
        material["materials"][f"{name}:{parent}"] = {
            "-states": ["EnableStencilTest", "StencilWrite"],
            "stencilWriteMask": 0, "stencilReadMask": 0,
            "frontFace": {"stencilFunc": "Always", "stencilFailOp": "Keep",
                          "stencilDepthFailOp": "Keep", "stencilPassOp": "Keep"},
            "backFace": {"stencilFunc": "Always", "stencilFailOp": "Keep",
                         "stencilDepthFailOp": "Keep", "stencilPassOp": "Keep"}}
    files["materials/entity.material"] = encoded(material)
    path = "render_controllers/weapons.render_controllers.json"
    controllers = json.loads(files[path])
    replacement = "variable.is_enchanted ? material.vv_item_clean_glint : material.vv_item_clean"
    for name, controller in controllers["render_controllers"].items():
        if name.endswith(".first_person"):
            continue
        old = controller["materials"][0]["*"]
        controller["materials"] = [{"*": replacement if name.endswith(".third_person")
            else f"c.is_first_person ? ({old}) : ({replacement})"}]
    files[path] = encoded(controllers)
    modified = []
    for path in list(files):
        if not path.startswith("attachables/") or not path.endswith(".json"):
            continue
        doc = json.loads(files[path]);d = doc.get("minecraft:attachable", {}).get("description", {})
        if "geyser_cooldown" not in str(d.get("render_controllers", [])):
            continue
        if d["materials"].get("default") != "entity_alphatest" or d["materials"].get("enchanted") != "entity_alphatest_glint":
            raise ValueError(f"Unexpected item material: {path}")
        d["materials"].update(vv_item_clean="vv_item_clean", vv_item_clean_glint="vv_item_clean_glint")
        files[path] = encoded(doc);modified.append(path)
    if len(modified) != 37:
        raise ValueError(f"Expected 37 existing cooldown items, found {len(modified)}")
    shield_source = (ROOT / "experiments/vv-held-item/shield.entity.json").read_bytes()
    shield = json.loads(shield_source)
    d = shield["minecraft:attachable"]["description"]
    original_shield_controllers = copy.deepcopy(d["render_controllers"])
    d["materials"].update(vv_item_clean="vv_item_clean", vv_item_clean_glint="vv_item_clean_glint")
    d["render_controllers"] = [{name: "c.is_first_person"} for name in original_shield_controllers]
    d["render_controllers"].append({"controller.render.vv_item_clean_shield": "!c.is_first_person"})
    files["attachables/vv_shield.entity.json"] = encoded(shield)
    files["render_controllers/vv_held_items.render_controllers.json"] = encoded({"format_version": "1.8.0",
        "render_controllers": {"controller.render.vv_item_clean_shield": {
            "geometry": "Geometry.default", "materials": [{"*": replacement}],
            "textures": ["Texture.default", "Texture.enchanted"]}}})
    files["licenses/vv-held-item-sources.json"] = (ROOT / "experiments/vv-held-item/sources.json").read_bytes()
    for name in original:
        if name in modified:
            old = json.loads(original[name]);new = json.loads(files[name])
            old["minecraft:attachable"]["description"].pop("materials")
            new["minecraft:attachable"]["description"].pop("materials")
            if old != new:
                raise ValueError(f"Existing item behavior changed: {name}")
        elif name not in {"materials/entity.material", "render_controllers/weapons.render_controllers.json"}:
            if files[name] != original[name]:
                raise ValueError(f"Unexpected body/armor/asset change: {name}")
    old_rc = json.loads(original["render_controllers/weapons.render_controllers.json"])["render_controllers"]
    new_rc = json.loads(files["render_controllers/weapons.render_controllers.json"])["render_controllers"]
    if old_rc["controller.render.geyser_cooldown.first_person"] != new_rc["controller.render.geyser_cooldown.first_person"]:
        raise ValueError("First-person weapon controller changed")
    manifest = json.loads(files["manifest.json"])
    manifest["header"].update(name="Cooldown + Glowing VV HELD ITEM PROTOTYPE 17",
        description="Stencil-neutral third-person sword/tool/shield materials; body remains prototype 16",
        uuid=str(uuid.uuid4()))
    for module in manifest["modules"]:
        module["uuid"] = str(uuid.uuid4())
    files["manifest.json"] = encoded(manifest)
    output.mkdir(parents=True, exist_ok=True)
    pack = output / "GeyserCooldownAnimation-VV-held-item-prototype-17.mcpack"
    with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, content in sorted(files.items()):z.writestr(name, content)
    jar = output / "GeyserCooldownAnimation-1.3.15-vv-prototype.17.jar"
    with zipfile.ZipFile(jar_source) as src, zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for member in src.infolist():
            content = src.read(member)
            if member.filename == "geyser-cooldown-animation.mcpack":content = pack.read_bytes()
            elif member.filename == "extension.yml":
                content = content.replace(b"version: 1.3.15", b"version: 1.3.15-vv-prototype.17")
            z.writestr(member, content)
    print(f"Prototype pack: {pack} ({pack.stat().st_size} bytes)")
    print(f"Prototype JAR: {jar}")
    print("37 existing held items + vanilla shield; existing item geometry/pose and body/armor unchanged")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pack-source", type=Path, required=True)
    p.add_argument("--extension-source", type=Path, required=True)
    p.add_argument("--output", type=Path, default=ROOT / "build/vv-outline-prototype")
    args = p.parse_args()
    build(args.pack_source, args.extension_source, args.output)
