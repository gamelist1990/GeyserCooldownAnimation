#!/usr/bin/env python3
"""Candidate 33: disable only armor-specific outline controllers; diagnostic control."""
import io,json,pathlib,uuid,zipfile
r=pathlib.Path(__file__).resolve().parents[2]/"build/bedrock-lab"
base=next((r/"variants/compact-armor-color").glob("GeyserCooldownAnimation-*.jar"))
out=r/"variants/armor-outline-isolation-33"
if out.exists():raise SystemExit("Existing variant, refusing overwrite")
with zipfile.ZipFile(base) as z: jar={k:z.read(k) for k in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar["geyser-cooldown-animation.mcpack"])) as z: pack={k:z.read(k) for k in z.namelist()}
changes=[]
for name in list(pack):
 if not name.startswith("attachables/") or not name.endswith(".json"):continue
 try: obj=json.loads(pack[name])
 except Exception:continue
 desc=obj.get("minecraft:attachable",{}).get("description",{})
 rc=desc.get("render_controllers")
 if not isinstance(rc,list):continue
 filtered=[]
 for item in rc:
  key=next(iter(item)) if isinstance(item,dict) and len(item)==1 else item if isinstance(item,str) else ""
  if key.startswith("controller.render.vv_native_armor_outline_") or key.startswith("controller.render.vv_bound_helmet_outline_"):
   changes.append((name,key))
  else:filtered.append(item)
 if len(filtered)!=len(rc):
  desc["render_controllers"]=filtered
  pack[name]=json.dumps(obj,separators=(",",":")).encode()
assert len(changes)>=20,changes
manifest=json.loads(pack["manifest.json"])
manifest["header"]["uuid"]=str(uuid.uuid4())
manifest["header"]["name"]="Glowing LAB armor isolate 33"
for m in manifest["modules"]:m["uuid"]=str(uuid.uuid4())
pack["manifest.json"]=json.dumps(manifest,separators=(",",":")).encode()
out.mkdir(parents=True)
with zipfile.ZipFile(out/"armor-outline-isolation-33.mcpack","w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for k,v in sorted(pack.items()):z.writestr(k,v)
jar["geyser-cooldown-animation.mcpack"]=(out/"armor-outline-isolation-33.mcpack").read_bytes()
old=b"version: 1.3.15-vv-lab.28"
assert jar["extension.yml"].count(old)==1
jar["extension.yml"]=jar["extension.yml"].replace(old,b"version: 1.3.15-vv-lab.33")
target=out/"GeyserCooldownAnimation-1.3.15-vv-lab.33.jar"
with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for k,v in sorted(jar.items()):z.writestr(k,v)
with zipfile.ZipFile(target) as z:assert z.testzip() is None
(out/"changes.json").write_text(json.dumps({"base":"candidate28","diagnostic_only":True,"disabled_armor_outline_controllers":len(changes),"changes":changes,"production_modified":False},indent=2)+"\n")
print("GENERATED",target,"controllers disabled",len(changes))
