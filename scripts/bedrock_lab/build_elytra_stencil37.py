#!/usr/bin/env python3
"""Lab-only candidate37: same animated Elytra geometry with inner stencil mask."""
import io,json,copy,uuid,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[2]/"build/bedrock-lab"
source=R/"variants/armor-dynamic-palette36/GeyserCooldownAnimation-1.3.15-vv-lab.36.jar"
out=R/"variants/elytra-stencil37"
if out.exists():raise SystemExit("candidate37 exists")
with zipfile.ZipFile(source) as z:jar={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar["geyser-cooldown-animation.mcpack"])) as z:pack={n:z.read(n) for n in z.namelist()}
geo="models/entity/elytra_outline.geo.json"
doc=json.loads(pack[geo])
original=doc["geometry.elytra_outline"]
inner=copy.deepcopy(original)
for bone in inner["bones"]:
 for cube in bone.get("cubes",[]):
  assert cube["inflate"]==1.2
  cube["inflate"]=0.45
doc["geometry.vv_elytra_mask"]=inner
pack[geo]=json.dumps(doc,separators=(",",":")).encode()
playerpath="entity/player.entity.json"
playerdoc=json.loads(pack[playerpath])
desc=playerdoc["minecraft:client_entity"]["description"]
assert "vv_elytra_mask" not in desc["geometry"]
desc["geometry"]["vv_elytra_mask"]="geometry.vv_elytra_mask"
desc["materials"].setdefault("vv_forward_mask","vv_forward_mask")
controllerpath="render_controllers/elytra/outline_elytra.render_controllers.json"
controllerdoc=json.loads(pack[controllerpath])
cid="controller.render.vv_elytra_stencil_mask"
assert cid not in controllerdoc["render_controllers"]
controllerdoc["render_controllers"][cid]={
  "geometry":"Geometry.vv_elytra_mask",
  "materials":[{"*":"Material.vv_forward_mask"}],
  "textures":["Texture.elytra"],
  "part_visibility":[{"*":True}],
  "rebuild_animation_matrices":True
}
pack[controllerpath]=json.dumps(controllerdoc,separators=(",",":")).encode()
rcs=desc["render_controllers"]
outline_keys=("controller.render.outline_elytra_layer_black_no_esp","controller.render.outline_elytra_layer_customization")
indices=[i for i,rc in enumerate(rcs) if isinstance(rc,dict) and any(x in rc for x in outline_keys)]
assert len(indices)==2,indices
on="!variable.is_first_person && query.is_item_name_any('slot.armor.chest', 0, 'minecraft:elytra') && q.property('glow:color') > 0 && q.property('glow:a') > 0"
rcs.insert(min(indices),{cid:on})
pack[playerpath]=json.dumps(playerdoc,separators=(",",":")).encode()
manifest=json.loads(pack["manifest.json"])
manifest["header"]["uuid"]=str(uuid.uuid4())
manifest["header"]["name"]="Glowing LAB Elytra stencil37"
for m in manifest["modules"]:m["uuid"]=str(uuid.uuid4())
pack["manifest.json"]=json.dumps(manifest,separators=(",",":")).encode()
out.mkdir(parents=True)
zpack=out/"elytra-stencil37.mcpack"
with zipfile.ZipFile(zpack,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(pack.items()):z.writestr(n,v)
jar["geyser-cooldown-animation.mcpack"]=zpack.read_bytes()
old=b"version: 1.3.15-vv-lab.36"
assert jar["extension.yml"].count(old)==1
jar["extension.yml"]=jar["extension.yml"].replace(old,b"version: 1.3.15-vv-lab.37")
zjar=out/"GeyserCooldownAnimation-1.3.15-vv-lab.37.jar"
with zipfile.ZipFile(zjar,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(jar.items()):z.writestr(n,v)
with zipfile.ZipFile(zjar) as z:assert z.testzip() is None
(out/"changes.json").write_text(json.dumps({"base":"candidate36","experiment":"mask elytra interior with stencil using same animated wing bones", "mask_inflate":0.45,"outer_inflate":1.2,"production_modified":False,"visual_status":"untested"},indent=2)+"\n")
print("GENERATED",zjar)
