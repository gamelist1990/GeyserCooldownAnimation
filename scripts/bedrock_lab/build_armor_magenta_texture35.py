#!/usr/bin/env python3
"""Candidate 35 tests armor outline tint driven by RGBA coverage texture."""
import io,json,pathlib,uuid,zipfile
from PIL import Image
r=pathlib.Path(__file__).resolve().parents[2]/"build/bedrock-lab"
base=next((r/"variants/compact-armor-color").glob("GeyserCooldownAnimation-*.jar"))
out=r/"variants/armor-texture-magenta35"
if out.exists():raise SystemExit("Existing candidate35")
with zipfile.ZipFile(base) as z:jar={k:z.read(k) for k in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar["geyser-cooldown-animation.mcpack"])) as z:pack={k:z.read(k) for k in z.namelist()}
changed=[]
for p in ("textures/entity/vv_native_coverage_1.png","textures/entity/vv_native_coverage_2.png"):
 image=Image.open(io.BytesIO(pack[p])).convert("RGBA")
 new=Image.new("RGBA",image.size,(255,0,255,0))
 new.putalpha(image.getchannel("A"))
 buf=io.BytesIO();new.save(buf,format="PNG",optimize=True)
 pack[p]=buf.getvalue()
 changed.append(p)
manifest=json.loads(pack["manifest.json"])
manifest["header"]["uuid"]=str(uuid.uuid4());manifest["header"]["name"]="Glowing LAB armor magenta texture 35"
for m in manifest["modules"]:m["uuid"]=str(uuid.uuid4())
pack["manifest.json"]=json.dumps(manifest,separators=(",",":")).encode()
out.mkdir(parents=True)
with zipfile.ZipFile(out/"armor-texture-magenta35.mcpack","w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for k,v in sorted(pack.items()):z.writestr(k,v)
jar["geyser-cooldown-animation.mcpack"]=(out/"armor-texture-magenta35.mcpack").read_bytes()
old=b"version: 1.3.15-vv-lab.28"
assert jar["extension.yml"].count(old)==1
jar["extension.yml"]=jar["extension.yml"].replace(old,b"version: 1.3.15-vv-lab.35")
target=out/"GeyserCooldownAnimation-1.3.15-vv-lab.35.jar"
with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for k,v in sorted(jar.items()):z.writestr(k,v)
with zipfile.ZipFile(target) as z:assert z.testzip() is None
(out/"changes.json").write_text(json.dumps({"base":"candidate28","diagnostic_only":True,"changes":changed,"test_color":"#FF00FF","goal":"Does RGBA texture drive armor outline hue, preserving original alpha cutout?","note":"Shared mask texture also recolored, but mask pass disables all color writes."},indent=2)+"\n")
print("GENERATED",target)
