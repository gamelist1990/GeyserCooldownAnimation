#!/usr/bin/env python3
"""LAB candidate42: color the native-animated Elytra outer silhouette with RGB444 palette."""
from pathlib import Path
import io,json,uuid,zipfile
from PIL import Image
r=Path(__file__).resolve().parents[2]/"build/bedrock-lab"
source=r/"variants/elytra-native-attachable41/GeyserCooldownAnimation-1.3.15-vv-lab.41.jar"
out=r/"variants/elytra-native-colored42"
assert not out.exists()
with zipfile.ZipFile(source) as z:jar={k:z.read(k) for k in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar["geyser-cooldown-animation.mcpack"])) as z:pack={k:z.read(k) for k in z.namelist()}
vanilla=r/"references/vanilla-elytra-mojang-sample.png"
original=Image.open(vanilla).convert("RGBA")
assert original.size==(64,32)
assert set(original.getchannel("A").getdata())=={0,255}
alpha=original.getchannel("A")
attach_name="attachables/elytra.json"
attach=json.loads(pack[attach_name])
d=attach["minecraft:attachable"]["description"]
for index in range(64):
    color=(((index//16)%4)*85,((index//4)%4)*85,(index%4)*85)
    im=Image.new("RGBA",original.size,(*color,0))
    im.putalpha(alpha)
    buf=io.BytesIO()
    im.save(buf,format="PNG",optimize=True)
    name=f"vv_elytra_palette_{index:02d}"
    assert name not in d["textures"]
    d["textures"][name]=f"textures/entity/{name}"
    pack[f"textures/entity/{name}.png"]=buf.getvalue()
pack[attach_name]=json.dumps(attach,separators=(",",":")).encode()
controller_name="render_controllers/elytra/outline_elytra.render_controllers.json"
doc=json.loads(pack[controller_name])
ctrl=doc["render_controllers"]["controller.render.vv_elytra_native_outline"]
ctrl["arrays"]={"textures":{"Array.vv_elytra_colors":[f"Texture.vv_elytra_palette_{i:02d}" for i in range(64)]}}
channel=lambda c:f"math.clamp(math.floor(q.property('glow:{c}') * 3.0 + 0.5), 0.0, 3.0)"
index=f"({channel('r')} * 16.0 + {channel('g')} * 4.0 + {channel('b')})"
ctrl["textures"]=[f"Array.vv_elytra_colors[{index}]"]
pack[controller_name]=json.dumps(doc,separators=(",",":")).encode()
manifest=json.loads(pack["manifest.json"])
manifest["header"]["uuid"]=str(uuid.uuid4())
manifest["header"]["name"]="GeyserGlow LAB native Elytra team-colors42"
for m in manifest["modules"]:m["uuid"]=str(uuid.uuid4())
pack["manifest.json"]=json.dumps(manifest,separators=(",",":")).encode()
out.mkdir(parents=True)
res=out/"elytra-native-colored42.mcpack"
with zipfile.ZipFile(res,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for k,v in sorted(pack.items()):z.writestr(k,v)
jar["geyser-cooldown-animation.mcpack"]=res.read_bytes()
assert jar["extension.yml"].count(b"version: 1.3.15-vv-lab.41")==1
jar["extension.yml"]=jar["extension.yml"].replace(b"version: 1.3.15-vv-lab.41",b"version: 1.3.15-vv-lab.42")
dest=out/"GeyserCooldownAnimation-1.3.15-vv-lab.42.jar"
with zipfile.ZipFile(dest,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for k,v in sorted(jar.items()):z.writestr(k,v)
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    with zipfile.ZipFile(io.BytesIO(z.read("geyser-cooldown-animation.mcpack"))) as rp:
        assert rp.testzip() is None
(out/"changes.json").write_text(json.dumps({"base":41,"palette_textures":64,"source":"Mojang bedrock-samples resource_pack/textures/models/armor/elytra.png; alpha-only derivative, lab only","alpha_binary":True,"selector":index,"visual_status":"untested","production_modified":False},indent=2)+"\n")
print("BUILT",dest,dest.stat().st_size)
