#!/usr/bin/env python3
"""LAB candidate 41: Render Elytra outline in the native attachable animation space.

The old player-mesh Elytra is disabled; matching bones are rendered on the actual
worn Elytra with shared Vanilla animation matrices and a dedicated stencil ring.
"""
from pathlib import Path
import io, json, uuid, zipfile

LAB = Path(__file__).resolve().parents[2] / "build/bedrock-lab"
base = LAB / "variants/armor-dynamic-palette36/GeyserCooldownAnimation-1.3.15-vv-lab.36.jar"
out = LAB / "variants/elytra-native-attachable41"
if out.exists(): raise SystemExit("Candidate 41 already exists")
with zipfile.ZipFile(base) as z: jar = {n: z.read(n) for n in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar["geyser-cooldown-animation.mcpack"])) as z:
    pack = {n: z.read(n) for n in z.namelist()}

# Exact Mojang vanilla cuboids: geometry.elytra from resource_pack/models/mobs.json.
def native_geo(inflate):
    return {
        "texturewidth":64,"textureheight":32,"visible_bounds_width":5,
        "visible_bounds_height":3.5,"visible_bounds_offset":[0,1.25,0],
        "bones":[
            {"name":"body","pivot":[0,24,0]},
            {"name":"left_wing","pivot":[0,24,0],"parent":"body",
             "cubes":[{"origin":[-10,0,0],"size":[10,20,2],"uv":[22,0],"inflate":inflate}]},
            {"name":"right_wing","pivot":[0,24,0],"parent":"body","mirror":True,
             "cubes":[{"origin":[0,0,0],"size":[10,20,2],"uv":[22,0],"inflate":inflate}]}
        ]
    }
geo_name = "models/entity/vv_native_elytra_layers.geo.json"
assert geo_name not in pack
pack[geo_name] = json.dumps({"format_version":"1.8.0",
                            "geometry.vv_native_elytra_outer":native_geo(0.58),
                            "geometry.vv_native_elytra_mask":native_geo(0.14)},
                           separators=(",",":")).encode()

attach_name = "attachables/elytra.json"
attach = json.loads(pack[attach_name])
d = attach["minecraft:attachable"]["description"]
d["geometry"]["vv_outline"] = "geometry.vv_native_elytra_outer"
d["geometry"]["vv_mask"] = "geometry.vv_native_elytra_mask"
d["materials"]["vv_mask"] = "vv_forward_mask"
d["materials"]["vv_outline"] = "vv_legacy_outline"
rcs = d["render_controllers"]
assert rcs == ["controller.render.gca_glowing_armor"]
condition = "q.property('glow:color') > 0 && q.property('glow:a') > 0"
rcs.extend([
    {"controller.render.vv_elytra_native_mask":condition},
    {"controller.render.vv_elytra_native_outline":condition}
])
pack[attach_name] = json.dumps(attach,separators=(",",":")).encode()

ctrl_name = "render_controllers/elytra/outline_elytra.render_controllers.json"
ctrl = json.loads(pack[ctrl_name])
controller = ctrl["render_controllers"]
controller["controller.render.vv_elytra_native_mask"] = {
    "geometry":"Geometry.vv_mask",
    "materials":[{"*":"Material.vv_mask"}],
    "textures":["Texture.default"],
    "part_visibility":[{"*":True}],
    "rebuild_animation_matrices":True
}
rgb = {key:f"q.property('glow:{key}')" for key in "rgba"}
controller["controller.render.vv_elytra_native_outline"] = {
    "geometry":"Geometry.vv_outline",
    "materials":[{"*":"Material.vv_outline"}],
    "textures":["Texture.default"],
    "part_visibility":[{"*":True}],
    "overlay_color":rgb,
    "is_hurt_color":rgb,
    "on_fire_color":rgb,
    "ignore_lighting":True,
    "rebuild_animation_matrices":True
}
pack[ctrl_name] = json.dumps(ctrl,separators=(",",":")).encode()

player_name = "entity/player.entity.json"
player = json.loads(pack[player_name])
renderers = player["minecraft:client_entity"]["description"]["render_controllers"]
removed = []
for rc in renderers:
    if not isinstance(rc,dict):continue
    for key in rc:
        if "elytra_stencil_mask" in key or "outline_elytra_layer_" in key:
            rc[key] = "0.0"
            removed.append(key)
assert len(removed)==2,removed
pack[player_name] = json.dumps(player,separators=(",",":")).encode()

manifest = json.loads(pack["manifest.json"])
manifest["header"]["uuid"] = str(uuid.uuid4())
manifest["header"]["name"] = "GeyserGlow native Elytra layers LAB41"
for m in manifest["modules"]:m["uuid"]=str(uuid.uuid4())
pack["manifest.json"]=json.dumps(manifest,separators=(",",":")).encode()
out.mkdir(parents=True)
res = out / "elytra-native-attachable41.mcpack"
with zipfile.ZipFile(res,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n,v in sorted(pack.items()):z.writestr(n,v)
jar["geyser-cooldown-animation.mcpack"] = res.read_bytes()
old=b"version: 1.3.15-vv-lab.36"
assert jar["extension.yml"].count(old)==1
jar["extension.yml"]=jar["extension.yml"].replace(old,b"version: 1.3.15-vv-lab.41")
jfile=out/"GeyserCooldownAnimation-1.3.15-vv-lab.41.jar"
with zipfile.ZipFile(jfile,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n,v in sorted(jar.items()):z.writestr(n,v)
with zipfile.ZipFile(jfile) as z:
    assert z.testzip() is None
    with zipfile.ZipFile(io.BytesIO(z.read("geyser-cooldown-animation.mcpack"))) as inner:
        assert inner.testzip() is None
(out/"changes.json").write_text(json.dumps({"base":"36","method":"Native Elytra attachable rendering",
"outer_inflate":0.58,"mask_inflate":0.14,"disables_player_elytra":removed,
"team_color":"overlay_color sourced from glow:r/g/b/a","status":"untested","production_modified":False},indent=2)+"\n")
print("BUILT",jfile,jfile.stat().st_size, "disabled",removed)
