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
          repaint_skin=False, depth_test_repaint=False, forward_mask=False,
          armor_masks=False, rebuild_pose=False, matched_mask_rigs=False,
          solid_armor_silhouettes=False):
    if solid_armor_silhouettes:
        matched_mask_rigs = True
    if matched_mask_rigs:
        rebuild_pose = True
    if rebuild_pose:
        armor_masks = True
    if armor_masks:
        forward_mask = True
    if forward_mask:
        depth_test_repaint = True
    if depth_test_repaint:
        repaint_skin = True
    revision = 12 if solid_armor_silhouettes else (11 if matched_mask_rigs else (10 if rebuild_pose else (9 if armor_masks else (8 if forward_mask else (7 if depth_test_repaint else (6 if repaint_skin else (5 if diagnose_skin_only else (4 if separate_body_mask else 3))))))))
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
    if armor_masks:
        slots = ("helmet", "chestplate", "leggings", "boots") if solid_armor_silhouettes else ("helmet", "chestplate")
        # Reference dimensions/UV: Mojang bedrock-samples player_armor.json.
        # Use the existing player skeleton so mask parts follow the same pose
        # as the user-confirmed outline models, without attachable offsets.
        skeleton = json.loads(stable["models/entity/wide_player_outline.geo.json"])["minecraft:geometry"][0]
        geometries = []
        visible_parts = {"helmet": {"head", "hat"}, "chestplate": {"body", "leftArm", "rightArm"},
                         "leggings": {"body", "leftLeg", "rightLeg"}, "boots": {"leftLeg", "rightLeg"}}
        for slot in slots:
            visible = visible_parts[slot]
            bones = []
            for old in skeleton["bones"]:
                if old["name"] not in {"root", "waist", "body", "head", "hat", "leftArm", "rightArm", "leftLeg", "rightLeg"}:
                    continue
                bone = {key: copy.deepcopy(value) for key, value in old.items()
                        if key in {"name", "parent", "pivot", "rotation"}}
                if old["name"] in visible:
                    if old["name"] == "hat":
                        cube = {"origin": [-4, 24, -4], "size": [8, 8, 8],
                                "uv": [32, 0], "inflate": 0.5}
                    else:
                        cube = copy.deepcopy(old["cubes"][0])
                        cube["inflate"] = 1.01 if old["name"] == "body" else 1.0
                        if old["name"] in {"leftArm", "rightArm"}:
                            cube["uv"] = [40, 16]
                            if old["name"] == "leftArm":
                                cube["mirror"] = True
                        if solid_armor_silhouettes:
                            if slot == "chestplate" and old["name"] in {"leftArm", "rightArm"}:
                                cube["origin"][1] = 19
                                cube["size"][1] = 5
                            elif slot == "leggings":
                                cube["inflate"] = 0.5 if old["name"] == "body" else 0.49
                                if old["name"] in {"leftLeg", "rightLeg"}:
                                    cube["origin"][1] = 3
                                    cube["size"][1] = 9
                            elif slot == "boots":
                                cube["size"][1] = 6
                                cube["inflate"] = 1.0
                            if old["name"] in {"leftLeg", "rightLeg"}:
                                cube["origin"][0] = -0.1 if old["name"] == "leftLeg" else -3.9
                    bone["cubes"] = [cube]
                bones.append(bone)
            geometries.append({"description": {"identifier": f"geometry.vv_armor_mask_{slot}",
                "texture_width": 64, "texture_height": 32, "visible_bounds_width": 5,
                "visible_bounds_height": 4, "visible_bounds_offset": [0, 1, 0]}, "bones": bones})
        files["models/entity/vv_armor_masks.geo.json"] = encoded(
            {"format_version": "1.12.0", "minecraft:geometry": geometries})
        definitions = {}
        for name, content in stable.items():
            if name.startswith("render_controllers/") and name.endswith(".json"):
                definitions.update(json.loads(content)["render_controllers"])
        player = json.loads(files["entity/player.entity.json"])
        description = player["minecraft:client_entity"]["description"]
        for slot in slots:
            description["geometry"][f"vv_armor_mask_{slot}"] = f"geometry.vv_armor_mask_{slot}"
        additions = []
        controllers = {}
        for entry in description["render_controllers"]:
            if not isinstance(entry, dict):
                continue
            for name, condition in entry.items():
                if not name.endswith("_layer_customization") or not name.startswith("controller.render.outline_"):
                    continue
                slot = next((slot for slot in slots if f"_{slot}_" in name), None)
                if not slot:
                    continue
                mask_name = "controller.render.vv_armor_mask_" + name.removeprefix("controller.render.outline_")
                controllers[mask_name] = {"geometry": f"Geometry.vv_armor_mask_{slot}",
                    "materials": [{"*": "Material.vv_forward_mask"}],
                    "textures": copy.deepcopy(definitions[name]["textures"]),
                    "part_visibility": [{"*": True}]}
                condition = condition.replace("q.property('glow:color') == 2", "q.property('glow:color') > 0")
                additions.append({mask_name: f"({condition}) && !variable.map_face_icon && !query.is_spectator && q.property('glow:a') > 0"})
        order = description["render_controllers"]
        index = next(i for i, entry in enumerate(order)
                     if isinstance(entry, dict) and any("outline" in key for key in entry))
        order[index:index] = additions
        files["entity/player.entity.json"] = encoded(player)
        files["render_controllers/vv_armor_masks.render_controllers.json"] = encoded(
            {"format_version": "1.8.0", "render_controllers": controllers})
        if solid_armor_silhouettes:
            from PIL import Image
            texture = io.BytesIO()
            Image.new("RGBA", (2, 2), (255, 255, 255, 255)).save(texture, format="PNG")
            files["textures/entity/vv_silhouette_mask.png"] = texture.getvalue()
            description["textures"]["vv_silhouette_mask"] = "textures/entity/vv_silhouette_mask"
            files["entity/player.entity.json"] = encoded(player)
            for path, content in list(files.items()):
                if not path.startswith("render_controllers/") or not path.endswith(".json"):
                    continue
                doc = json.loads(content)
                changed = False
                for key, controller in doc["render_controllers"].items():
                    if key.startswith("controller.render.vv_armor_mask_") or (
                            key.startswith("controller.render.outline_") and any(f"_{slot}_" in key for slot in slots)):
                        controller["textures"] = ["Texture.vv_silhouette_mask"]
                        changed = True
                if changed:
                    files[path] = encoded(doc)
    if matched_mask_rigs:
        player = json.loads(files["entity/player.entity.json"])
        description = player["minecraft:client_entity"]["description"]
        for kind, source_name in [("slim", "player_outline.geo.json"),
                                  ("wide", "wide_player_outline.geo.json")]:
            geometry = json.loads(stable[f"models/entity/{source_name}"])
            model = geometry["minecraft:geometry"][0]
            identifier = f"geometry.vv_body_mask_{kind}"
            model["description"]["identifier"] = identifier
            # Same bone order, pivots, cube UVs and parent transforms as outline.
            # Remove only outline expansion so the mask is the inner surface.
            for bone in model["bones"]:
                bone.pop("inflate", None)
                for cube in bone.get("cubes", []):
                    cube["inflate"] = 0.0
            files[f"models/entity/vv_body_mask_{kind}.geo.json"] = encoded(geometry)
            description["geometry"][f"vv_body_mask_{kind}"] = identifier
        files["entity/player.entity.json"] = encoded(player)
        path = "render_controllers/player.render_controllers.json"
        controllers = json.loads(files[path])
        mask = controllers["render_controllers"]["controller.render.vv_forward_mask"]
        mask["arrays"] = {"geometries": {"Array.vv_body_masks":
            ["Geometry.vv_body_mask_slim", "Geometry.vv_body_mask_wide"]}}
        mask["geometry"] = "Array.vv_body_masks[variable.slim ? 0 : 1]"
        mask["part_visibility"] = [{"*": True}]
        files[path] = encoded(controllers)
        # Keep the armor mask's full bone order aligned with the armor outline,
        # even when most bones carry no mask cubes.
        path = "models/entity/vv_armor_masks.geo.json"
        masks = json.loads(files[path])
        for model in masks["minecraft:geometry"]:
            original_bones = json.loads(stable["models/entity/player_armor_2.json" if model["description"]["identifier"].endswith("leggings") else "models/entity/player_armor_1.json"])["minecraft:geometry"][0]["bones"]
            cubes = {bone["name"]: bone["cubes"] for bone in model["bones"] if bone.get("cubes")}
            model["bones"] = [{key: copy.deepcopy(value) for key, value in bone.items()
                               if key != "cubes"} for bone in original_bones]
            for bone in model["bones"]:
                if bone["name"] in cubes:
                    bone["cubes"] = cubes[bone["name"]]
                    if solid_armor_silhouettes:
                        for cube in bone["cubes"]:
                            cube["uv"] = {face: {"uv": [0, 0], "uv_size": [2, 2]}
                                          for face in ("north", "east", "south", "west", "up", "down")}
                    elif bone["name"] in {"leftArm", "rightArm"}:
                        # Sleeve bottom cap must not punch out the bare hand's
                        # contour. Side UVs still preserve texture alpha holes.
                        bone["cubes"][0]["uv"] = {
                            "north": {"uv": [44, 20], "uv_size": [4, 12]},
                            "east": {"uv": [40, 20], "uv_size": [4, 12]},
                            "south": {"uv": [52, 20], "uv_size": [4, 12]},
                            "west": {"uv": [48, 20], "uv_size": [4, 12]},
                            "up": {"uv": [44, 16], "uv_size": [4, 4]}}
        files[path] = encoded(masks)
    if rebuild_pose:
        # Default skin, compact armor mask, and the fragmented outline have
        # different bone arrays. Request matrices for each third-person geometry
        # rather than depending on another controller's cached bone transforms.
        # The first-person controller and shared attachable controllers stay as-is.
        for name, content in list(files.items()):
            if not name.startswith("render_controllers/") or not name.endswith(".json"):
                continue
            doc = json.loads(content)
            changed = False
            for key, controller in doc["render_controllers"].items():
                if "first_person" not in key and (
                        "outline" in key or key.startswith("controller.render.vv_")
                        or key == "controller.render.player.third_person"):
                    controller["rebuild_animation_matrices"] = True
                    changed = True
            if changed:
                files[name] = encoded(doc)
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
                elif key in {"controller.render.armor", "controller.render.gca_glowing_armor", "controller.render.player.cape"}:
                    original = json.loads(stable[name])["render_controllers"][key]["materials"][0]["*"]
                    vanilla = ("variable.is_enchanted ? Material.enchanted : Material.default"
                               if key in {"controller.render.armor", "controller.render.gca_glowing_armor"} else "Material.default")
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
                    if armor_masks and key == "minecraft:client_entity":
                        for slot in slots:
                            after[key]["description"]["geometry"].pop(f"vv_armor_mask_{slot}")
                        after[key]["description"]["render_controllers"] = [
                            entry for entry in after[key]["description"]["render_controllers"]
                            if not isinstance(entry, dict) or not any(
                                name.startswith("controller.render.vv_armor_mask_") for name in entry)]
                    if matched_mask_rigs and key == "minecraft:client_entity":
                        for kind in ("slim", "wide"):
                            after[key]["description"]["geometry"].pop(f"vv_body_mask_{kind}")
                    if solid_armor_silhouettes and key == "minecraft:client_entity":
                        after[key]["description"]["textures"].pop("vv_silhouette_mask")
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
    parser.add_argument("--armor-masks", action="store_true",
                        help="Prototype 9: extend prototype 8 with helmet and chestplate silhouette masks")
    parser.add_argument("--rebuild-pose", action="store_true",
                        help="Prototype 10: rebuild matrices for each third-person mask/outline geometry")
    parser.add_argument("--matched-mask-rigs", action="store_true",
                        help="Prototype 11: mask bone layouts match legacy outlines; remove sleeve mask bottom caps")
    parser.add_argument("--solid-armor-silhouettes", action="store_true",
                        help="Prototype 12: opaque equipment silhouettes, with sleeve/legging/boot extents")
    args = parser.parse_args()
    if sum([args.separate_body_mask, args.diagnose_skin_only, args.repaint_skin,
            args.depth_test_repaint, args.forward_mask, args.armor_masks, args.rebuild_pose,
            args.matched_mask_rigs, args.solid_armor_silhouettes]) > 1:
        parser.error("Choose one experiment")
    build(args.extension_source, args.output, args.separate_body_mask,
          args.diagnose_skin_only, args.repaint_skin, args.depth_test_repaint,
          args.forward_mask, args.armor_masks, args.rebuild_pose, args.matched_mask_rigs,
          args.solid_armor_silhouettes)
