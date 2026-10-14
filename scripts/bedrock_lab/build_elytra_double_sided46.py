#!/usr/bin/env python3
"""Lab 46 diagnostic: double-sided native Elytra stencil coverage.

No expanded wing should remain after a correctly ordered matching stencil mask.
This isolates geometry/pose mismatch from stencil execution. Not a release.
"""
from pathlib import Path
import io,json,uuid,zipfile
root=Path(__file__).resolve().parents[2]/'build/bedrock-lab'
source=root/'variants/elytra-native-identity44/GeyserCooldownAnimation-1.3.15-vv-lab.44.jar'
out=root/'variants/elytra-double-sided46'
if out.exists():raise ValueError('Use a new experiment')
with zipfile.ZipFile(source) as z:jar={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar['geyser-cooldown-animation.mcpack'])) as z:pack={n:z.read(n) for n in z.namelist()}
before=pack.copy()
path='render_controllers/elytra/outline_elytra.render_controllers.json'
d=json.loads(pack[path])
d['render_controllers']['controller.render.vv_elytra_native_mask']['materials']=[{'*':'Material.vv_elytra_mask_double'}]
n='materials/entity.material'
mats=json.loads(pack[n]);base=mats['materials']['vv_forward_mask:entity_alphablend']
import copy
local=copy.deepcopy(base)
local['-states']=[x for x in local.get('-states',[]) if x!='DisableCulling']
local['+states'].append('DisableCulling')
mats['materials']['vv_elytra_mask_double:entity_alphablend']=local
pack[n]=json.dumps(mats,separators=(',',':')).encode()
n='attachables/elytra.json';attach=json.loads(pack[n])
attach['minecraft:attachable']['description']['materials']['vv_elytra_mask_double']='vv_elytra_mask_double'
pack[n]=json.dumps(attach,separators=(',',':')).encode()
pack[path]=json.dumps(d,separators=(',',':')).encode()
m=json.loads(pack['manifest.json']);m['header']['uuid']=str(uuid.uuid4());m['header']['name']='GeyserGlow LAB native double sided diagnostic46'
for module in m['modules']:module['uuid']=str(uuid.uuid4())
pack['manifest.json']=json.dumps(m,separators=(',',':')).encode()
changed=[n for n in pack if pack[n]!=before[n]]
assert set(changed)=={path,'manifest.json','materials/entity.material','attachables/elytra.json'}
out.mkdir(parents=True)
res=out/'elytra-double-sided46.mcpack'
with zipfile.ZipFile(res,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(pack.items()):z.writestr(n,v)
jar['geyser-cooldown-animation.mcpack']=res.read_bytes()
assert jar['extension.yml'].count(b'version: 1.3.15-vv-lab.44')==1
jar['extension.yml']=jar['extension.yml'].replace(b'version: 1.3.15-vv-lab.44',b'version: 1.3.15-vv-lab.46')
j=out/'GeyserCooldownAnimation-1.3.15-vv-lab.46.jar'
with zipfile.ZipFile(j,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(jar.items()):z.writestr(n,v)
(out/'changes.json').write_text(json.dumps({'base':44,'changed':changed,'diagnostic':True,'expected':'No expanded Elytra silhouette from identical native surfaces','visual_status':'not_tested'},indent=2)+'\n')
print(j)
