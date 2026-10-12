#!/usr/bin/env python3
"""Prototype 3: keep stable outline geometry/algorithm, adapt material bindings.

Builds from the stable release JAR. Does not modify release source assets or
deploy anything. VV stencil support is unverified; this is a client experiment.
"""
import argparse
import copy
import io
import json
from pathlib import Path
import uuid
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ALIASES = {"outline_base": "vv_legacy_base", "outline": "vv_legacy_outline",
           "outline_no_esp": "vv_legacy_no_esp", "enchanted_base": "vv_legacy_armor"}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def build(source, output, separate_body_mask=False, diagnose_skin_only=False,
          repaint_skin=False, depth_test_repaint=False, forward_mask=False):
    if forward_mask:
        depth_test_repaint = True
    if depth_test_repaint:
        repaint_skin = True
    revision = 8 if forward_mask else (7 if depth_test_repaint else (6 if repaint_skin else (5 if diagnose_skin_only else (4 if separate_body_mask else 3))))
    with zipfile.ZipFile(source) as jar:
        with zipfile.ZipFile(io.BytesIO(jar.read("geyser-cooldown-animation.mcpack"))) as pack:
            files = {name: pack.read(name) for name in pack.namelist()}
    stable = files.copy()
    material = json.loads(files["materials/entity.material"])
    definitions = material["materials"]
    for original, new in [
            ("outline_base:entity_alphatest", "vv_legacy_base:entity_alphatest"),
            ("outline_base_armor:entity_alphatest", "vv_legacy_armor:entity_alphatest"),
            ("outline:entity_static", "vv_legacy_outline:entity_alphablend"),
            ("outline_no_esp:entity_static", "vv_legacy_no_esp:entity_alphablend")]:
        candidate = copy.deepcopy(definitions[original])
        candidate.pop("stencilReadMark", None)
        candidate["stencilReadMask"] = 32
        candidate["stencilWriteMask"] = 0 if "entity_static" in original else 32
        if "entity_static" in original:
            candidate["+defines"].append("ALPHA_TEST")
            candidate["-states"].append("StencilWrite")
        definitions[new] = candidate
    files["materials/entity.material"] = encoded(material)
    for name, content in list(files.items()):
        if not name.endswith(".json"):
            continue
        if name.startswith(("entity/", "attachables/")):
            doc = json.loads(content)
            entity = doc.get("minecraft:client_entity", doc.get("minecraft:attachable"))
            if not entity:
                continue
            materials = entity["description"].get("materials", {})
            additions = {}
            for old, new in ALIASES.items():
                if old in materials:
                    additions[new] = new
            if materials.get("cape") == "outline_base":
                additions["vv_legacy_base"] = "vv_legacy_base"
            if additions:
                materials.update(additions)
                files[name] = encoded(doc)
        elif name.startswith("render_controllers/"):
            doc = json.loads(content)
            changed = False
            for controller_name, controller in doc.get("render_controllers", {}).items():
                if "first_person" in controller_name:
                    continue
                for entry in controller.get("materials", []):
                    for key, expression in list(entry.items()):
                        replacement = expression
                        # Replace longer names first; preserve default materials.
                        for old in sorted(ALIASES, key=len, reverse=True):
                            replacement = replacement.replace("Material." + old, "Material." + ALIASES[old])
                        replacement = replacement.replace("Material.cape", "Material.vv_legacy_base")
                        if replacement == expression:
                            continue
                        if "outline" in controller_name or "third_person" in controller_name:
                            entry[key] = replacement
                        else:
                            entry[key] = f"variable.is_first_person ? ({expression}) : ({replacement})"
                        changed = True
            if changed:
                files[name] = encoded(doc)
    if separate_body_mask:
        # Separate the visible skin from the custom stencil material. This
        # isolates missing base rendering from an overlay that covers it.
        mask = copy.deepcopy(definitions["vv_legacy_base:entity_alphatest"])
        mask["+states"] += ["DisableColorWrite", "DisableDepthWrite"]
        for face in ("frontFace", "backFace"):
            mask[face]["stencilFailOp"] = "Keep"
            mask[face]["stencilDepthFailOp"] = "Keep"
        definitions["vv_legacy_mask:entity_alphatest"] = mask
        files["materials/entity.material"] = encoded(material)
        name = "render_controllers/player.render_controllers.json"
        controllers = json.loads(files[name])
        body = controllers["render_controllers"]["controller.render.player.third_person"]
        body["materials"] = [{"*": "Material.default"}]
        mask_controller = copy.deepcopy(body)
        mask_controller["materials"] = [{"*": "Material.vv_legacy_mask"}]
        controllers["render_controllers"]["controller.render.vv_legacy_body_mask"] = mask_controller
        files[name] = encoded(controllers)
        name = "entity/player.entity.json"
        player = json.loads(files[name])
        description = player["minecraft:client_entity"]["description"]
        description["materials"]["vv_legacy_mask"] = "vv_legacy_mask"
        order = description["render_controllers"]
        body_entry = next(entry for entry in order
                          if isinstance(entry, dict) and "controller.render.player.third_person" in entry)
        order.insert(order.index(body_entry) + 1, {"controller.render.vv_legacy_body_mask":
            "!variable.is_first_person && !variable.map_face_icon && !query.is_spectator && q.property('glow:color') > 0"})
        files[name] = encoded(player)
    if repaint_skin:
        # Diagnostic 5 showed that the vanilla skin is present. Attempt a final
        # skin composite over the legacy shell, without relying on stencil.
        # Always-depth is experimental in VV and may expose skin behind walls.
        definitions["vv_legacy_skin_front:entity_alphablend"] = {
            "+defines": ["ALPHA_TEST"],
            "+states": ["DisableDepthWrite"],
            "-states": ["DisableCulling", "EnableStencilTest", "StencilWrite"],
            "depthFunc": "LessEqual" if depth_test_repaint else "Always"}
        files["materials/entity.material"] = encoded(material)
        name = "render_controllers/player.render_controllers.json"
        controllers = json.loads(files[name])
        body = controllers["render_controllers"]["controller.render.player.third_person"]
        body["materials"] = [{"*": "Material.default"}]
        front = copy.deepcopy(body)
        front["materials"] = [{"*": "Material.vv_legacy_skin_front"}]
        controllers["render_controllers"]["controller.render.vv_legacy_skin_front"] = front
        files[name] = encoded(controllers)
        name = "entity/player.entity.json"
        player = json.loads(files[name])
        description = player["minecraft:client_entity"]["description"]
        description["materials"]["vv_legacy_skin_front"] = "vv_legacy_skin_front"
        description["render_controllers"].append({"controller.render.vv_legacy_skin_front":
            "!variable.is_first_person && !variable.map_face_icon && !query.is_spectator && q.property('glow:color') > 0 && q.property('glow:a') > 0"})
        files[name] = encoded(player)
    if forward_mask:
        # Prototype 7 confirms terrain occlusion for the skin. Attempt the
        # stencil write in the same alphablend family as the outline instead of
        # relying on the opaque player's stencil surviving between passes.
        # Write the body silhouette even behind terrain, but no color or depth.
        face = {"stencilFunc": "Always", "stencilFailOp": "Keep",
                "stencilDepthFailOp": "Keep", "stencilPassOp": "Replace"}
        definitions["vv_forward_mask:entity_alphablend"] = {
            "+defines": ["ALPHA_TEST"],
            "+states": ["EnableStencilTest", "StencilWrite", "DisableColorWrite", "DisableDepthWrite"],
            "-states": ["DisableCulling"], "depthFunc": "Always",
            "frontFace": copy.deepcopy(face), "backFace": copy.deepcopy(face),
            "stencilRef": 32, "stencilReadMask": 32, "stencilWriteMask": 32}
        # Both face directions must reject the interior; VV may not apply the
        # old material's inverted-culling state in the same way as classic.
        for key in ("vv_legacy_outline:entity_alphablend", "vv_legacy_no_esp:entity_alphablend"):
            for side in ("frontFace", "backFace"):
                definitions[key][side] = {"stencilFunc": "NotEqual", "stencilFailOp": "Keep",
                    "stencilDepthFailOp": "Keep", "stencilPassOp": "Keep"}
        files["materials/entity.material"] = encoded(material)
        name = "render_controllers/player.render_controllers.json"
        controllers = json.loads(files[name])
        mask_controller = copy.deepcopy(controllers["render_controllers"]["controller.render.player.third_person"])
        mask_controller["materials"] = [{"*": "Material.vv_forward_mask"}]
        controllers["render_controllers"]["controller.render.vv_forward_mask"] = mask_controller
        files[name] = encoded(controllers)
        name = "entity/player.entity.json"
        player = json.loads(files[name])
        description = player["minecraft:client_entity"]["description"]
        description["materials"]["vv_forward_mask"] = "vv_forward_mask"
        order = description["render_controllers"]
        index = next(i for i, entry in enumerate(order)
                     if isinstance(entry, dict) and any("outline" in key for key in entry))
        order.insert(index, {"controller.render.vv_forward_mask":
            "!variable.is_first_person && !variable.map_face_icon && !query.is_spectator && q.property('glow:color') > 0 && q.property('glow:a') > 0"})
        files[name] = encoded(player)
    if diagnose_skin_only:
        name = "entity/player.entity.json"
        player = json.loads(files[name])
        # Keep the effect/properties intact; suppress only third-person overlays
        # so the same glowing skin can be inspected without a covering shell.
        for entry in player["minecraft:client_entity"]["description"]["render_controllers"]:
            if isinstance(entry, dict):
                for key in entry:
                    if "outline" in key:
                        entry[key] = "0.0"
        files[name] = encoded(player)
        for name, content in list(files.items()):
            if not name.startswith("render_controllers/") or not name.endswith(".json"):
                continue
            doc = json.loads(content)
            changed = False
            for key, controller in doc["render_controllers"].items():
                if key == "controller.render.player.third_person":
                    controller["materials"] = [{"*": "Material.default"}]
                    changed = True
                elif key in {"controller.render.armor", "controller.render.player.cape"}:
                    original = json.loads(stable[name])["render_controllers"][key]["materials"][0]["*"]
                    vanilla = ("variable.is_enchanted ? Material.enchanted : Material.default"
                               if key == "controller.render.armor" else "Material.default")
                    controller["materials"] = [{"*": f"variable.is_first_person ? ({original}) : ({vanilla})"}]
                    changed = True
            if changed:
                files[name] = encoded(doc)
    manifest = json.loads(files["manifest.json"])
    manifest["header"].update(name=f"Cooldown + Glowing VV LEGACY PROTOTYPE {revision}",
        description=("DIAGNOSTIC: third-person glow overlays disabled; inspect visible skin"
                     if diagnose_skin_only else "Original stencil outline geometry with experimental VV material bindings"),
        uuid=str(uuid.uuid4()), min_engine_version=[1, 21, 120])
    for module in manifest["modules"]:
        module["uuid"] = str(uuid.uuid4())
    manifest["capabilities"] = ["pbr"]
    files["manifest.json"] = encoded(manifest)
    # Build invariants: no hull models, texture changes, motion changes or
    # first-person controller edits. Material aliases are the only entity edit.
    for name in stable:
        if name.startswith(("models/", "textures/", "animations/", "animation_controllers/")):
            if files[name] != stable[name]:
                raise ValueError(f"Unexpected stable asset change: {name}")
        if name.startswith(("entity/", "attachables/")) and name.endswith(".json"):
            before = json.loads(stable[name]); after = json.loads(files[name])
            for key in ("minecraft:client_entity", "minecraft:attachable"):
                if key in before:
                    before[key]["description"].pop("materials", None)
                    after[key]["description"].pop("materials", None)
                    if separate_body_mask and key == "minecraft:client_entity":
                        after[key]["description"]["render_controllers"] = [
                            entry for entry in after[key]["description"]["render_controllers"]
                            if not isinstance(entry, dict) or "controller.render.vv_legacy_body_mask" not in entry]
                    if diagnose_skin_only and key == "minecraft:client_entity":
                        for entry in before[key]["description"]["render_controllers"]:
                            if isinstance(entry, dict):
                                for controller in entry:
                                    if "outline" in controller:
                                        entry[controller] = "0.0"
                    if repaint_skin and key == "minecraft:client_entity":
                        after[key]["description"]["render_controllers"] = [
                            entry for entry in after[key]["description"]["render_controllers"]
                            if not isinstance(entry, dict) or "controller.render.vv_legacy_skin_front" not in entry]
                    if forward_mask and key == "minecraft:client_entity":
                        after[key]["description"]["render_controllers"] = [
                            entry for entry in after[key]["description"]["render_controllers"]
                            if not isinstance(entry, dict) or "controller.render.vv_forward_mask" not in entry]
            if before != after:
                raise ValueError(f"Unexpected entity/attachable behavior change: {name}")
        if name.startswith("render_controllers/") and name.endswith(".json"):
            before = json.loads(stable[name])["render_controllers"]
            after = json.loads(files[name])["render_controllers"]
            for key in before:
                if "first_person" in key and before[key] != after[key]:
                    raise ValueError(f"First-person controller changed: {key}")
    output.mkdir(parents=True, exist_ok=True)
    pack_path = output / f"GeyserCooldownAnimation-VV-legacy-prototype-{revision}.mcpack"
    with zipfile.ZipFile(pack_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as pack:
        for name, content in sorted(files.items()):
            pack.writestr(name, content)
    jar_path = output / f"GeyserCooldownAnimation-1.3.15-vv-prototype.{revision}.jar"
    with zipfile.ZipFile(source) as stable_jar, zipfile.ZipFile(
            jar_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as jar:
        for member in stable_jar.infolist():
            content = stable_jar.read(member)
            if member.filename == "geyser-cooldown-animation.mcpack":
                content = pack_path.read_bytes()
            elif member.filename == "extension.yml":
                content = content.replace(b"version: 1.3.15", f"version: 1.3.15-vv-prototype.{revision}".encode())
            jar.writestr(member, content)
    print(f"Prototype pack: {pack_path} ({pack_path.stat().st_size} bytes)")
    print(f"Prototype JAR: {jar_path}")
    print("Stable geometry/textures/motion and first-person controllers preserved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extension-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "build/vv-outline-prototype")
    parser.add_argument("--separate-body-mask", action="store_true",
                        help="Prototype 4: draw skin with vanilla material and stencil mask separately")
    parser.add_argument("--diagnose-skin-only", action="store_true",
                        help="Prototype 5 DIAGNOSTIC: disable third-person overlays to inspect the skin")
    parser.add_argument("--repaint-skin", action="store_true",
                        help="Prototype 6: restore legacy outlines and composite vanilla skin last")
    parser.add_argument("--depth-test-repaint", action="store_true",
                        help="Prototype 7: keep the skin composite, but let terrain occlude it")
    parser.add_argument("--forward-mask", action="store_true",
                        help="Prototype 8: stencil body mask in the same material family as the outline")
    args = parser.parse_args()
    if sum([args.separate_body_mask, args.diagnose_skin_only, args.repaint_skin,
            args.depth_test_repaint, args.forward_mask]) > 1:
        parser.error("Choose one experiment")
    build(args.extension_source, args.output, args.separate_body_mask,
          args.diagnose_skin_only, args.repaint_skin, args.depth_test_repaint, args.forward_mask)
