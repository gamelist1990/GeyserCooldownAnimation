#!/usr/bin/env python3
"""Candidate 38: shrink the Elytra ring thickness and animation Z exaggeration."""
import io,json,uuid,zipfile
from pathlib import Path
r=Path(__file__).resolve().parents[2]/"build/bedrock-lab"
source=r/"variants/elytra-stencil37/GeyserCooldownAnimation-1.3.15-vv-lab.37.jar"
dest=r/"variants/elytra-thin-ring38"
if dest.exists():raise SystemExit("Already exists")
with zipfile.ZipFile(source) as z:jar={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar["geyser-cooldown-animation.mcpack"])) as z:pack={n:z.read(n) for n in z.namelist()}
geometry="models/entity/elytra_outline.geo.json"
doc=json.loads(pack[geometry])
for key,inflate in (("geometry.elytra_outline",0.35),("geometry.vv_elytra_mask",0.12)):
  assert key in doc
  for bone in doc[key]["bones"]:
    for cube in bone.get("cubes",[]):cube["inflate"]=inflate
pack[geometry]=json.dumps(doc,separators=(",",":")).encode()
anim="animations/elytra_outline.animation.json"
doc=json.loads(pack[anim])
for val in doc["animations"].values():
 for name,pose in val["bones"].items():
  if name=="body":pose["scale"]=1.012
  elif "wing" in name:
   assert pose["scale"]==[1,1,2]
   pose["scale"]=[1,1,1.08]
pack[anim]=json.dumps(doc,separators=(",",":")).encode()
manifest=json.loads(pack["manifest.json"])
manifest["header"]["uuid"]=str(uuid.uuid4());manifest["header"]["name"]="Glowing LAB Elytra thin ring38"
for m in manifest["modules"]:m["uuid"]=str(uuid.uuid4())
pack["manifest.json"]=json.dumps(manifest,separators=(",",":")).encode()
dest.mkdir(parents=True)
resource=dest/"elytra-thin-ring38.mcpack"
with zipfile.ZipFile(resource,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(pack.items()):z.writestr(n,v)
jar["geyser-cooldown-animation.mcpack"]=resource.read_bytes()
old=b"version: 1.3.15-vv-lab.37"
assert jar["extension.yml"].count(old)==1
jar["extension.yml"]=jar["extension.yml"].replace(old,b"version: 1.3.15-vv-lab.38")
target=dest/"GeyserCooldownAnimation-1.3.15-vv-lab.38.jar"
with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(jar.items()):z.writestr(n,v)
with zipfile.ZipFile(target) as z:assert z.testzip() is None
(dest/"changes.json").write_text(json.dumps({"base":"candidate37","elytra_outline_inflate":0.35,"elytra_mask_inflate":0.12,"body_scale":1.012,"wing_depth_scale":1.08,"scope":"lab only","status":"untested"},indent=2)+"\n")
print("GENERATED",target)
