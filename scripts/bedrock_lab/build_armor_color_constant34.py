#!/usr/bin/env python3
"""Candidate 34 diagnostic: force pure magenta on all armor colored outline controllers."""
import io,json,pathlib,uuid,zipfile
r=pathlib.Path(__file__).resolve().parents[2]/"build/bedrock-lab"
base=next((r/"variants/compact-armor-color").glob("GeyserCooldownAnimation-*.jar"))
out=r/"variants/armor-color-constant34"
if out.exists():raise SystemExit("Existing candidate 34")
with zipfile.ZipFile(base) as z: jar={k:z.read(k) for k in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar["geyser-cooldown-animation.mcpack"])) as z:pack={k:z.read(k) for k in z.namelist()}
changed={}
magenta={"r":1.0,"g":0.0,"b":1.0,"a":1.0}
for name in ("render_controllers/vv_native_armor.render_controllers.json","render_controllers/vv_bound_helmet.render_controllers.json"):
 obj=json.loads(pack[name])
 for key,ctrl in obj["render_controllers"].items():
  if not key.endswith("_outline_color"):continue
  for attr in ("color","overlay_color","is_hurt_color","on_fire_color"):
   assert attr in ctrl
   ctrl[attr]=magenta.copy()
  changed[key]=name
 pack[name]=json.dumps(obj,separators=(",",":")).encode()
assert len(changed)==2
manifest=json.loads(pack["manifest.json"])
manifest["header"]["uuid"]=str(uuid.uuid4());manifest["header"]["name"]="Glowing LAB armor static magenta 34"
for m in manifest["modules"]:m["uuid"]=str(uuid.uuid4())
pack["manifest.json"]=json.dumps(manifest,separators=(",",":")).encode()
out.mkdir(parents=True)
with zipfile.ZipFile(out/"armor-color-constant34.mcpack","w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for k,v in sorted(pack.items()):z.writestr(k,v)
jar["geyser-cooldown-animation.mcpack"]=(out/"armor-color-constant34.mcpack").read_bytes()
old=b"version: 1.3.15-vv-lab.28"
assert jar["extension.yml"].count(old)==1
jar["extension.yml"]=jar["extension.yml"].replace(old,b"version: 1.3.15-vv-lab.34")
target=out/"GeyserCooldownAnimation-1.3.15-vv-lab.34.jar"
with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for k,v in sorted(jar.items()):z.writestr(k,v)
with zipfile.ZipFile(target) as z:assert z.testzip() is None
(out/"changes.json").write_text(json.dumps({"base":"candidate28","diagnostic_only":True,"changed":changed,"override_rgba":magenta,"hypothesis":"if armor changes from white to magenta, variable color path fails; else color attr/material is ignored"},indent=2)+"\n")
print("GENERATED",target)
