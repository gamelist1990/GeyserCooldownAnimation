#!/usr/bin/env python3
"""Candidate 50: normal Elytra, no wing outline, stencil-neutral third person."""
from pathlib import Path
import io,json,uuid,zipfile
root=Path(__file__).resolve().parents[2]/'build/bedrock-lab'
source=root/'variants/armor-dynamic-palette36/GeyserCooldownAnimation-1.3.15-vv-lab.36.jar'
out=root/'variants/elytra-passthrough50'
if out.exists():raise ValueError('Candidate already exists')
with zipfile.ZipFile(source) as z:jar={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar['geyser-cooldown-animation.mcpack'])) as z:pack={n:z.read(n) for n in z.namelist()}
before=pack.copy()
def save(path,d):pack[path]=json.dumps(d,separators=(',',':')).encode()
p='entity/player.entity.json';d=json.loads(pack[p]);desc=d['minecraft:client_entity']['description']
count=0
for rc in desc['render_controllers']:
 if isinstance(rc,dict):
  for name in rc:
   if name.startswith('controller.render.outline_elytra_'):rc[name]='0';count+=1
assert count==2
for a in desc['scripts']['animate']:
 if isinstance(a,dict) and 'elytra_default_controller' in a:
  a['elytra_default_controller']='variable.is_first_person && ('+a['elytra_default_controller']+')'
save(p,d)
p='attachables/elytra.json';d=json.loads(pack[p]);desc=d['minecraft:attachable']['description']
desc['materials'].update({'vv_clean':'vv_item_clean','vv_clean_glint':'vv_item_clean_glint'})
desc['render_controllers']=['controller.render.gca_elytra_passthrough']
save(p,d)
# Keep the first-person branch exactly as in candidate 36.
fp="variable.is_first_person ? ((variable.is_enchanted ? (q.property('glow:color') == 0 ? Material.enchanted : Material.enchanted_base) : (q.property('glow:color') == 0 ? Material.default : Material.outline_base))) : (variable.is_enchanted ? Material.vv_clean_glint : Material.vv_clean)"
save('render_controllers/elytra_passthrough.render_controllers.json',{'format_version':'1.8.0','render_controllers':{'controller.render.gca_elytra_passthrough':{'geometry':'Geometry.default','materials':[{'*':fp}],'textures':['Texture.default','Texture.enchanted']}}})
man=json.loads(pack['manifest.json']);man['header']['uuid']=str(uuid.uuid4());man['header']['name']='GeyserGlow LAB normal Elytra50'
for m in man['modules']:m['uuid']=str(uuid.uuid4())
save('manifest.json',man)
out.mkdir(parents=True);rp=out/'elytra-passthrough50.mcpack'
with zipfile.ZipFile(rp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(pack.items()):z.writestr(n,v)
jar['geyser-cooldown-animation.mcpack']=rp.read_bytes();jar['extension.yml']=jar['extension.yml'].replace(b'version: 1.3.15-vv-lab.36',b'version: 1.3.15-vv-lab.50')
j=out/'GeyserCooldownAnimation-1.3.15-vv-lab.50.jar'
with zipfile.ZipFile(j,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(jar.items()):z.writestr(n,v)
changed=[n for n in pack if pack[n]!=before.get(n)]
assert set(changed)=={'entity/player.entity.json','attachables/elytra.json','render_controllers/elytra_passthrough.render_controllers.json','manifest.json'}
for path in (rp,j):
 with zipfile.ZipFile(path) as z:assert z.testzip() is None
(out/'changes.json').write_text(json.dumps({'base':36,'changed':changed,'requirement':'Normal visible Elytra; no wing glow; player outline passes through wings','visual_status':'review_required'},indent=2)+'\n')
print(j)
