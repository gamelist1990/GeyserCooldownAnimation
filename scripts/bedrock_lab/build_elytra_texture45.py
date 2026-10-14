#!/usr/bin/env python3
"""Lab 45 diagnostic: identical native geometry and palette texture for both passes.

No expanded wing should remain after a correctly ordered matching stencil mask.
This isolates geometry/pose mismatch from stencil execution. Not a release.
"""
from pathlib import Path
import io,json,uuid,zipfile
root=Path(__file__).resolve().parents[2]/'build/bedrock-lab'
source=root/'variants/elytra-native-identity44/GeyserCooldownAnimation-1.3.15-vv-lab.44.jar'
out=root/'variants/elytra-identical-texture45'
if out.exists():raise ValueError('Use a new experiment')
with zipfile.ZipFile(source) as z:jar={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar['geyser-cooldown-animation.mcpack'])) as z:pack={n:z.read(n) for n in z.namelist()}
before=pack.copy()
path='render_controllers/elytra/outline_elytra.render_controllers.json'
d=json.loads(pack[path])
for name in ('controller.render.vv_elytra_native_mask','controller.render.vv_elytra_native_outline'):
 d['render_controllers'][name]['geometry']='Geometry.default'
mask=d['render_controllers']['controller.render.vv_elytra_native_mask']
outer=d['render_controllers']['controller.render.vv_elytra_native_outline']
mask['arrays']=outer['arrays']
mask['textures']=outer['textures']
pack[path]=json.dumps(d,separators=(',',':')).encode()
m=json.loads(pack['manifest.json']);m['header']['uuid']=str(uuid.uuid4());m['header']['name']='GeyserGlow LAB native identical texture diagnostic45'
for module in m['modules']:module['uuid']=str(uuid.uuid4())
pack['manifest.json']=json.dumps(m,separators=(',',':')).encode()
changed=[n for n in pack if pack[n]!=before[n]]
assert set(changed)=={path,'manifest.json'}
out.mkdir(parents=True)
res=out/'elytra-identical-texture45.mcpack'
with zipfile.ZipFile(res,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(pack.items()):z.writestr(n,v)
jar['geyser-cooldown-animation.mcpack']=res.read_bytes()
assert jar['extension.yml'].count(b'version: 1.3.15-vv-lab.44')==1
jar['extension.yml']=jar['extension.yml'].replace(b'version: 1.3.15-vv-lab.44',b'version: 1.3.15-vv-lab.45')
j=out/'GeyserCooldownAnimation-1.3.15-vv-lab.45.jar'
with zipfile.ZipFile(j,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(jar.items()):z.writestr(n,v)
(out/'changes.json').write_text(json.dumps({'base':44,'changed':changed,'diagnostic':True,'expected':'No expanded Elytra silhouette from identical native surfaces','visual_status':'not_tested'},indent=2)+'\n')
print(j)
