#!/usr/bin/env python3
"""Candidate 40: align both Elytra passes in the same vanilla-scale pose.

Lab-only. No claims of visual parity until real Bedrock captures are reviewed.
"""
import io,json,uuid,zipfile
from pathlib import Path
r=Path(__file__).resolve().parents[2]/"build/bedrock-lab"
src=r/"variants/elytra-balanced39/GeyserCooldownAnimation-1.3.15-vv-lab.39.jar"
out=r/"variants/elytra-aligned40"
if out.exists():raise SystemExit("Candidate 40 already exists; refusing overwrite")
with zipfile.ZipFile(src) as z: jar={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar["geyser-cooldown-animation.mcpack"])) as z:pack={n:z.read(n) for n in z.namelist()}
geo_name="models/entity/elytra_outline.geo.json"
geo=json.loads(pack[geo_name])
for key,inflate in (("geometry.elytra_outline",0.48),("geometry.vv_elytra_mask",0.24)):
    for bone in geo[key]["bones"]:
        for cube in bone.get("cubes",[]):
            assert cube["size"]==[10,20,2],cube
            cube["inflate"]=inflate
pack[geo_name]=json.dumps(geo,separators=(",",":")).encode()
animation_name="animations/elytra_outline.animation.json"
anim=json.loads(pack[animation_name])
for value in anim["animations"].values():
    for bone,pose in value["bones"].items():
        if bone=="body":pose["scale"]=1.0
        elif "wing" in bone:pose["scale"]=[1,1,1]
pack[animation_name]=json.dumps(anim,separators=(",",":")).encode()
manifest=json.loads(pack["manifest.json"])
manifest["header"]["uuid"]=str(uuid.uuid4())
manifest["header"]["name"]="Glowing LAB Elytra aligned40"
for m in manifest["modules"]:m["uuid"]=str(uuid.uuid4())
pack["manifest.json"]=json.dumps(manifest,separators=(",",":")).encode()
out.mkdir(parents=True)
res=out/"elytra-aligned40.mcpack"
with zipfile.ZipFile(res,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n,v in sorted(pack.items()):z.writestr(n,v)
jar["geyser-cooldown-animation.mcpack"]=res.read_bytes()
old=b"version: 1.3.15-vv-lab.39"
assert jar["extension.yml"].count(old)==1
jar["extension.yml"]=jar["extension.yml"].replace(old,b"version: 1.3.15-vv-lab.40")
target=out/"GeyserCooldownAnimation-1.3.15-vv-lab.40.jar"
with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n,v in sorted(jar.items()):z.writestr(n,v)
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    with zipfile.ZipFile(io.BytesIO(z.read("geyser-cooldown-animation.mcpack"))) as pack:
        assert pack.testzip() is None
(out/"changes.json").write_text(json.dumps({
    "base":"candidate39","intent":"remove animation scale distortions, tighten shared stencil/outer silhouette",
    "outer_inflate":0.48,"mask_inflate":0.24,"body_scale":1.0,"wing_scale":[1,1,1],
    "geometry_preserved":"two 10x20x2 wing cuboids","production_modified":False,
    "visual_status":"untested; must compare against Bedrock vanilla elytra from all angles"
},indent=2)+"\n")
print("BUILT",target,"bytes",target.stat().st_size)
