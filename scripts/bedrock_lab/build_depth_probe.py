import io, json, pathlib, uuid, zipfile
root=pathlib.Path("/home/pexserver/WorkSpace/DevBox/GeyserCooldownAnimation/build/bedrock-lab")
src=root/"variants/compact-armor-color/GeyserCooldownAnimation-1.3.15-vv-lab.28.jar"
dst=root/"variants/depth-test-29"
dst.mkdir(exist_ok=False)
with zipfile.ZipFile(src) as z: entries={k:z.read(k) for k in z.namelist()}
with zipfile.ZipFile(io.BytesIO(entries["geyser-cooldown-animation.mcpack"])) as z: pack={k:z.read(k) for k in z.namelist()}
path="materials/entity.material"
m=json.loads(pack[path])
assert m["materials"]["vv_legacy_outline:entity_alphablend"]["depthFunc"]=="Always"
m["materials"]["vv_legacy_outline:entity_alphablend"]["depthFunc"]="LessEqual"
pack[path]=json.dumps(m,separators=(",",":")).encode()
manifest=json.loads(pack["manifest.json"]);manifest["header"]["uuid"]=str(uuid.uuid4())
for module in manifest["modules"]:module["uuid"]=str(uuid.uuid4())
manifest["header"]["name"]="Glowing LAB depth29";pack["manifest.json"]=json.dumps(manifest,separators=(",",":")).encode()
p=dst/"depth-test-29.mcpack"
with zipfile.ZipFile(p,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for k,v in sorted(pack.items()):z.writestr(k,v)
entries["geyser-cooldown-animation.mcpack"]=p.read_bytes()
assert b"1.3.15-vv-lab.28" in entries["extension.yml"]
entries["extension.yml"]=entries["extension.yml"].replace(b"1.3.15-vv-lab.28",b"1.3.15-vv-lab.29")
jar=dst/"GeyserCooldownAnimation-1.3.15-vv-lab.29.jar"
with zipfile.ZipFile(jar,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for k,v in sorted(entries.items()):z.writestr(k,v)
(dst/"changes.json").write_text(json.dumps({"base":"compact-armor-color (28)","experiment":"Only vv_legacy_outline depthFunc: Always -> LessEqual","target":"test shield occlusion","production_modified":False},indent=2))
print(jar)
