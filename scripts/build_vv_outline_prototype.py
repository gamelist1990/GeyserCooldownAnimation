#!/usr/bin/env python3
"""Build an isolated inverted-mesh experiment; never change stable pack assets.

This is a client-rendering experiment, not a verified Vibrant Visuals fix.
It deliberately starts with the six bare-player body parts. Equipment, capes,
custom skin geometry and through-wall outlines need separate client evaluation.
"""
import argparse
import copy
import io
import json
from pathlib import Path
import uuid
import zipfile

from PIL import Image
from compact_resource_pack import compact_json


ROOT = Path(__file__).resolve().parents[1]
BODY = {"body", "head", "leftArm", "rightArm", "leftLeg", "rightLeg"}
PARENTS = BODY | {"root", "waist"}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def inverted_box(cube, inflate, reverse_winding):
    """Closed shell with explicit inward winding and inward vertex normals.

    Culling is supplied by vanilla entity_alphatest, rather than custom material
    states. Faces behind the normal skin should fail the ordinary depth test.
    Actual Bedrock mesh winding/culling still requires a client check.
    """
    low = [v - inflate for v in cube["origin"]]
    high = [v + s + inflate for v, s in zip(cube["origin"], cube["size"])]
    positions = [[high[0] if x else low[0], high[1] if y else low[1],
                  high[2] if z else low[2]]
                 for x, y, z in [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                                 (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]]
    # These windings face inward in model coordinates. UVs sample solid color.
    faces = [[0, 1, 2, 3], [5, 4, 7, 6], [4, 0, 3, 7],
             [1, 5, 6, 2], [3, 2, 6, 7], [4, 5, 1, 0]]
    if reverse_winding:
        # Revision 1 filled the body on the user's VV client. Reverse vertex
        # order only to isolate the engine's front-face convention. Keep
        # inward lighting normals, dimensions, textures and depth unchanged.
        faces = [list(reversed(face)) for face in faces]
    normals = [[0, 0, 1], [0, 0, -1], [1, 0, 0], [-1, 0, 0],
               [0, -1, 0], [0, 1, 0]]
    return {"normalized_uvs": True, "positions": positions, "normals": normals,
            "uvs": [[0.5, 0.5]],
            "polys": [[[vertex, normal, 0] for vertex in face]
                      for normal, face in enumerate(faces)]}


def body_geometry(source, identifier, thickness, reverse_winding):
    old = json.loads(source)["minecraft:geometry"][0]
    description = copy.deepcopy(old["description"])
    description.update(identifier=identifier, texture_width=4, texture_height=4)
    bones = []
    for original in old["bones"]:
        if original["name"] not in PARENTS:
            continue
        bone = {key: copy.deepcopy(value) for key, value in original.items()
                if key in {"name", "parent", "pivot", "rotation"}}
        if original["name"] in BODY:
            bone["poly_mesh"] = inverted_box(original["cubes"][0], thickness, reverse_winding)
        bones.append(bone)
    return {"format_version": "1.14.0", "minecraft:geometry": [
        {"description": description, "bones": bones}]}


def build(output, thickness, extension_source, revision):
    files = {str(p.relative_to(ROOT / "resource-pack")): p.read_bytes()
             for p in (ROOT / "resource-pack").rglob("*") if p.is_file()}
    player = json.loads(files["entity/player.entity.json"])
    desc = player["minecraft:client_entity"]["description"]
    # Only third-person render selection and new resource aliases are changed.
    # The scripts, animation aliases, attachables and first-person controllers
    # are inherited from the user-confirmed stable pack.
    selected = []
    for entry in desc["render_controllers"]:
        name = next(iter(entry)) if isinstance(entry, dict) else entry
        if "outline" not in name:
            selected.append(entry)
    guard = ("!variable.is_first_person && !variable.map_face_icon && "
             "!query.is_spectator && q.property('glow:color') > 0 && "
             "q.property('glow:a') > 0")
    for kind, condition, original in [
            ("slim", "variable.slim", "player_outline.geo.json"),
            ("wide", "variable.wide", "wide_player_outline.geo.json")]:
        identifier = f"geometry.vv_prototype_{kind}"
        desc["geometry"][f"vv_{kind}"] = identifier
        files[f"models/entity/vv_prototype_{kind}.geo.json"] = encoded(
            body_geometry(files[f"models/entity/{original}"], identifier, thickness,
                          reverse_winding=revision == 2))
        selected.append({f"controller.render.vv_prototype_{kind}":
                         f"{condition} && {guard}"})
    desc["render_controllers"] = selected
    desc["materials"]["vv_outline"] = "entity_alphatest"
    # Four levels per channel preserve the Java team's sixteen standard colors.
    # Arbitrary custom RGB is approximated in this first diagnostic prototype.
    aliases = []
    for index in range(64):
        rgb = ((index // 16) * 85, ((index // 4) % 4) * 85, (index % 4) * 85)
        stem = f"vv_outline_{index}"
        path = f"textures/entity/vv_prototype/{stem}"
        desc["textures"][stem] = path
        aliases.append(f"Texture.{stem}")
        image = io.BytesIO()
        Image.new("RGBA", (4, 4), (*rgb, 255)).save(image, format="PNG")
        files[path + ".png"] = image.getvalue()
        files[path + ".texture_set.json"] = encoded({"format_version": "1.16.100",
            "minecraft:texture_set": {"color": stem,
                "metalness_emissive_roughness": [0, 255, 255]}})
    files["entity/player.entity.json"] = encoded(player)
    rc_path = "render_controllers/player.render_controllers.json"
    controllers = json.loads(files[rc_path])
    controllers["render_controllers"]["controller.render.player.third_person"][
        "materials"] = [{"*": "Material.default"}]
    files[rc_path] = encoded(controllers)
    # Stop the old stencil material on visible third-person armor/capes too.
    # First-person material choices retain their original expressions.
    rc_path = "render_controllers/armor/armor.render_controllers.json"
    controllers = json.loads(files[rc_path])
    armor = controllers["render_controllers"]["controller.render.armor"]
    old_material = armor["materials"][0]["*"]
    armor["materials"] = [{"*": f"variable.is_first_person ? {old_material} : "
                           "(variable.is_enchanted ? Material.enchanted : Material.default)"}]
    files[rc_path] = encoded(controllers)
    rc_path = "render_controllers/cape/cape.render_controllers.json"
    controllers = json.loads(files[rc_path])
    cape = controllers["render_controllers"]["controller.render.player.cape"]
    original = cape["materials"][0]["*"]
    cape["materials"] = [{"*": f"variable.is_first_person ? ({original}) : Material.default"}]
    files[rc_path] = encoded(controllers)
    index = ("q.property('glow:color') == 1 ? 0 : "
             "(math.round(q.property('glow:r') * 3) * 16 + "
             "math.round(q.property('glow:g') * 3) * 4 + "
             "math.round(q.property('glow:b') * 3))")
    controllers = {}
    for kind in ["slim", "wide"]:
        controllers[f"controller.render.vv_prototype_{kind}"] = {
            "arrays": {"textures": {"Array.vv_colors": aliases}},
            "geometry": f"Geometry.vv_{kind}",
            "materials": [{"*": "Material.vv_outline"}],
            "textures": [f"Array.vv_colors[{index}]"],
            "part_visibility": [{"*": True}], "ignore_lighting": True}
    files["render_controllers/vv_prototype.render_controllers.json"] = encoded(
        {"format_version": "1.8.0", "render_controllers": controllers})
    manifest = json.loads(files["manifest.json"])
    manifest["header"].update(
        name=f"Cooldown + Glowing VV body outline PROTOTYPE {revision}",
        description="Experimental inverted mesh; equipment outline pending",
        uuid=str(uuid.uuid4()), version=[1, 3, 15], min_engine_version=[1, 21, 120])
    manifest["capabilities"] = ["pbr"]
    for module in manifest["modules"]:
        module.update(uuid=str(uuid.uuid4()), version=[1, 3, 15])
    files["manifest.json"] = encoded(manifest)
    output.mkdir(parents=True, exist_ok=True)
    pack = output / f"GeyserCooldownAnimation-VV-outline-prototype-{revision}.mcpack"
    with zipfile.ZipFile(pack, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(files.items()):
            if name.endswith((".json", ".material")):
                content = compact_json(content)
            archive.writestr(name, content)
    if extension_source:
        # A local staging artifact only; production extension files untouched.
        jar = output / f"GeyserCooldownAnimation-1.3.15-vv-prototype.{revision}.jar"
        with zipfile.ZipFile(extension_source) as stable, zipfile.ZipFile(
                jar, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as candidate:
            for member in stable.infolist():
                content = stable.read(member)
                if member.filename == "geyser-cooldown-animation.mcpack":
                    content = pack.read_bytes()
                elif member.filename == "extension.yml":
                    content = content.replace(b"version: 1.3.15", f"version: 1.3.15-vv-prototype.{revision}".encode())
                candidate.writestr(member, content)
    print(f"Prototype only: {pack} ({pack.stat().st_size} bytes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build/vv-outline-prototype")
    parser.add_argument("--thickness", type=float, default=0.65)
    parser.add_argument("--extension-source", type=Path)
    parser.add_argument("--revision", type=int, choices=[1, 2], default=2)
    args = parser.parse_args()
    if not 0 < args.thickness <= 1:
        parser.error("thickness must be greater than zero and at most one model unit")
    build(args.output, args.thickness, args.extension_source, args.revision)
