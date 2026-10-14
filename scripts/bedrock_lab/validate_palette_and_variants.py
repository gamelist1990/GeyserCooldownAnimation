#!/usr/bin/env python3
"""Static pack checks for team palette, slim renderer, and elytra experiment variants."""
from pathlib import Path
import zipfile,io,json
from PIL import Image
root=Path(__file__).resolve().parents[2]/"build/bedrock-lab"
jar=root/"variants/armor-dynamic-palette36/GeyserCooldownAnimation-1.3.15-vv-lab.36.jar"
with zipfile.ZipFile(jar) as j,zipfile.ZipFile(io.BytesIO(j.read("geyser-cooldown-animation.mcpack"))) as pack:
  attachments=0
  for f in pack.namelist():
    if not f.startswith("attachables/") or not f.endswith(".json"):continue
    desc=json.loads(pack.read(f)).get("minecraft:attachable",{}).get("description",{})
    tx=desc.get("textures",{})
    if "vv_native_coverage" not in tx:continue
    for i in range(64):
      name=f"vv_glow_palette_{i:02d}"
      assert name in tx,(f,i)
      assert tx[name]+".png" in pack.namelist(),(f,name)
    attachments+=1
  assert attachments==29,attachments
  for uv in (1,2):
    base=Image.open(io.BytesIO(pack.read(f"textures/entity/vv_native_coverage_{uv}.png"))).convert("RGBA")
    for i in range(64):
      name=f"textures/entity/vv_glow_palette_{uv}_{i:02d}.png"
      image=Image.open(io.BytesIO(pack.read(name))).convert("RGBA")
      assert image.size==base.size and image.getchannel("A").tobytes()==base.getchannel("A").tobytes(),name
      expect=(((i//16)%4)*85,((i//4)%4)*85,(i%4)*85)
      assert image.getpixel((0,0))[:3]==expect,(name,image.getpixel((0,0)))
  for model in ("wide","slim"):
    path="models/entity/wide_player_outline.geo.json" if model=="wide" else "models/entity/player_outline.geo.json"
    doc=json.loads(pack.read(path)); geo=doc["minecraft:geometry"][0]
    b={bone["name"]:bone for bone in geo["bones"]}
    width=b["leftArm"]["cubes"][0]["size"][0]
    assert width==(4 if model=="wide" else 3)
    controllers="render_controllers/wide/outline_wide_player.render_controllers.json" if model=="wide" else "render_controllers/slim/outline_player.render_controllers.json"
    assert len(json.loads(pack.read(controllers))["render_controllers"])==2
  print("PALETTE_STATIC_PASS attachables=",attachments," textures=128"," model_shapes=wide,slim")
for n in (37,38,39):
  jar=root/f"variants/{ {37:'elytra-stencil37',38:'elytra-thin-ring38',39:'elytra-balanced39'}[n]}/GeyserCooldownAnimation-1.3.15-vv-lab.{n}.jar"
  with zipfile.ZipFile(jar) as z:
    assert z.testzip() is None
    with zipfile.ZipFile(io.BytesIO(z.read("geyser-cooldown-animation.mcpack"))) as pack:
      assert pack.testzip() is None
      geo=json.loads(pack.read("models/entity/elytra_outline.geo.json"))
      assert "geometry.vv_elytra_mask" in geo
  print("ELYTRA_ARCHIVE_PASS",n)
