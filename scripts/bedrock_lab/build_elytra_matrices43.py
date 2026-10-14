#!/usr/bin/env python3
"""LAB candidate43: test attachable native animation bone caching (no rebuild matrices)."""
from pathlib import Path
import io,json,uuid,zipfile
r=Path(__file__).resolve().parents[2]/"build/bedrock-lab"
src=r/"variants/elytra-native-colored42/GeyserCooldownAnimation-1.3.15-vv-lab.42.jar"
out=r/"variants/elytra-animation-matrices43"
assert not out.exists()
with zipfile.ZipFile(src) as z:jar={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar["geyser-cooldown-animation.mcpack"])) as z:pack={n:z.read(n) for n in z.namelist()}
n="render_controllers/elytra/outline_elytra.render_controllers.json"
doc=json.loads(pack[n])
for key in ("controller.render.vv_elytra_native_mask","controller.render.vv_elytra_native_outline"):
    c=doc["render_controllers"][key]
    assert c.pop("rebuild_animation_matrices")==True
pack[n]=json.dumps(doc,separators=(",",":")).encode()
man=json.loads(pack["manifest.json"]);man["header"]["uuid"]=str(uuid.uuid4())
man["header"]["name"]="GeyserGlow Elytra animation sharing LAB43"
for m in man["modules"]:m["uuid"]=str(uuid.uuid4())
pack["manifest.json"]=json.dumps(man,separators=(",",":")).encode()
out.mkdir(parents=True)
res=out/"elytra-animation-matrices43.mcpack"
with zipfile.ZipFile(res,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n,v in sorted(pack.items()):z.writestr(n,v)
jar["geyser-cooldown-animation.mcpack"]=res.read_bytes()
old=b"version: 1.3.15-vv-lab.42"
assert jar["extension.yml"].count(old)==1
jar["extension.yml"]=jar["extension.yml"].replace(old,b"version: 1.3.15-vv-lab.43")
dest=out/"GeyserCooldownAnimation-1.3.15-vv-lab.43.jar"
with zipfile.ZipFile(dest,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n,v in sorted(jar.items()):z.writestr(n,v)
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
(out/"changes.json").write_text(json.dumps({"base":42,"change":"omit rebuild_animation_matrices from both Elytra attachable controllers","status":"untested","production_modified":False},indent=2)+"\n")
print("BUILT",dest)
