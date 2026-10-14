#!/usr/bin/env python3
"""Build isolated motion/armor diagnostics from candidate 50 without FP edits."""
import argparse,io,json,uuid,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--candidate',type=int,required=True);p.add_argument('--shared-matrices',action='store_true');p.add_argument('--covered-parts',action='store_true');p.add_argument('--native-mask',action='store_true');p.add_argument('--simple-pants-mask',action='store_true');a=p.parse_args()
r=Path(__file__).resolve().parents[2]/'build/bedrock-lab';src=r/'variants/elytra-passthrough50/GeyserCooldownAnimation-1.3.15-vv-lab.50.jar';out=r/f'variants/motion-fix{a.candidate}'
assert not out.exists()
with zipfile.ZipFile(src) as z:jar={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar['geyser-cooldown-animation.mcpack'])) as z:pack={n:z.read(n) for n in z.namelist()}
before=pack.copy()
for path in list(pack):
 if not path.startswith('render_controllers/') or not path.endswith('.json'):continue
 d=json.loads(pack[path]);changed=False
 for name,rc in d.get('render_controllers',{}).items():
  body=name in ('controller.render.vv_forward_mask','controller.render.outline_layer_customization','controller.render.outline_layer_black_no_esp','controller.render.wide_outline_layer_customization','controller.render.wide_outline_layer_black_no_esp','controller.render.vv_legacy_skin_front')
  if name == 'controller.render.vv_forward_mask' and a.native_mask:
   rc['geometry']='Geometry.default';rc.pop('arrays',None);changed=True
  if body and a.shared_matrices:rc['rebuild_animation_matrices']=False;changed=True
  if body and 'outline_layer' in name and a.covered_parts:
   # Visibility is per bone; animated parents remain available to descendants.
   vis=[{'*':True},{'head':"!query.is_item_name_any('slot.armor.head', 0, 'minecraft:leather_helmet','minecraft:chainmail_helmet','minecraft:iron_helmet','minecraft:golden_helmet','minecraft:diamond_helmet','minecraft:netherite_helmet','minecraft:copper_helmet','minecraft:turtle_helmet')"}, {'hat*':"!query.is_item_name_any('slot.armor.head', 0, 'minecraft:leather_helmet','minecraft:chainmail_helmet','minecraft:iron_helmet','minecraft:golden_helmet','minecraft:diamond_helmet','minecraft:netherite_helmet','minecraft:copper_helmet','minecraft:turtle_helmet')"}]
   chest="!query.is_item_name_any('slot.armor.chest', 0, 'minecraft:leather_chestplate','minecraft:chainmail_chestplate','minecraft:iron_chestplate','minecraft:golden_chestplate','minecraft:diamond_chestplate','minecraft:netherite_chestplate','minecraft:copper_chestplate')"
   legs="!query.is_item_name_any('slot.armor.legs', 0, 'minecraft:leather_leggings','minecraft:chainmail_leggings','minecraft:iron_leggings','minecraft:golden_leggings','minecraft:diamond_leggings','minecraft:netherite_leggings','minecraft:copper_leggings')"
   vis += [{'body':chest},{'jacket*':chest},{'leftLeg':legs},{'rightLeg':legs},{'leftPants*':legs},{'rightPants*':legs}]
   rc['part_visibility']=vis;changed=True
 if changed:pack[path]=json.dumps(d,separators=(',',':')).encode()
if a.simple_pants_mask:
 for shape in ('slim','wide'):
  path=f'models/entity/vv_body_mask_{shape}.geo.json';d=json.loads(pack[path])
  for g in d['minecraft:geometry']:
   for b in g['bones']:
    if 'Pants' in b['name']:b.pop('cubes',None)
    if b['name'] in ('leftPants','rightPants'):
     left=b['name']=='leftPants';b['cubes']=[{'origin':[0 if left else -4,0,-2],'size':[4,12,4],'inflate':0.25,'uv':[0,48] if left else [0,32]}]
  pack[path]=json.dumps(d,separators=(',',':')).encode()
m=json.loads(pack['manifest.json']);m['header']['uuid']=str(uuid.uuid4());m['header']['name']=f'GeyserGlow LAB motion fix{a.candidate}'
for module in m['modules']:module['uuid']=str(uuid.uuid4())
pack['manifest.json']=json.dumps(m,separators=(',',':')).encode();out.mkdir(parents=True);rp=out/f'motion-fix{a.candidate}.mcpack'
with zipfile.ZipFile(rp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(pack.items()):z.writestr(n,v)
jar['geyser-cooldown-animation.mcpack']=rp.read_bytes();assert jar['extension.yml'].count(b'version: 1.3.15-vv-lab.50')==1;jar['extension.yml']=jar['extension.yml'].replace(b'version: 1.3.15-vv-lab.50',f'version: 1.3.15-vv-lab.{a.candidate}'.encode())
j=out/f'GeyserCooldownAnimation-1.3.15-vv-lab.{a.candidate}.jar'
with zipfile.ZipFile(j,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(jar.items()):z.writestr(n,v)
(out/'changes.json').write_text(json.dumps({'base':50,'options':vars(a),'changed':[n for n in pack if pack[n]!=before[n]],'visual_status':'untested'},indent=2)+'\n');print(j)
