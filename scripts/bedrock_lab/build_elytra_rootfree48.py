#!/usr/bin/env python3
"""LAB 48: preserve native Elytra pose while moving root scale into wing bones.

Uniform root scale commutes with wing rotation: scale the wing translation and
local scale by the same scalar. This avoids an accumulating actor/root scale
without changing cubes, UV, wing rotation, state controller, or visible shape.
Built only after the explicit matrix-reuse diagnostic; not a release.
"""
from pathlib import Path
import copy,io,json,uuid,zipfile
r=Path(__file__).resolve().parents[2]/'build/bedrock-lab'
source=r/'variants/elytra-explicit-shared47/GeyserCooldownAnimation-1.3.15-vv-lab.47.jar'
out=r/'variants/elytra-rootfree48'
if out.exists():raise ValueError('Experiment already exists')
with zipfile.ZipFile(source) as z:jar={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(io.BytesIO(jar['geyser-cooldown-animation.mcpack'])) as z:pack={n:z.read(n) for n in z.namelist()}
before=pack.copy()
original=json.loads((r/'references/client-elytra/vanilla-elytra.animation.json').read_text())
animations={}
for name,animation in original['animations'].items():
    updated=copy.deepcopy(animation);bones=updated['bones']
    assert bones['body']=={'scale':1.067}, (name,bones['body'])
    del bones['body']
    for wing in ('left_wing','right_wing'):
        bone=bones[wing]
        assert bone['scale']==[1,1,2]
        assert all(isinstance(v,(int,float)) for v in bone['position'])
        bone['position']=[v*1.067 for v in bone['position']]
        bone['scale']=[v*1.067 for v in bone['scale']]
        assert bone['rotation']==animation['bones'][wing]['rotation']
    animations[name.replace('animation.elytra.','animation.gca_vv_elytra.')]=updated
new='animations/vv_native_elytra_rootfree.animation.json'
assert new not in pack
pack[new]=json.dumps({'format_version':'1.8.0','animations':animations},separators=(',',':')).encode()
path='attachables/elytra.json';d=json.loads(pack[path]);aliases=d['minecraft:attachable']['description']['animations']
for name in ('default','gliding','sneaking','sleeping','swimming'):
    assert aliases[name]=='animation.elytra.'+name
    aliases[name]='animation.gca_vv_elytra.'+name
pack[path]=json.dumps(d,separators=(',',':')).encode()
# All native wing pivots coincide with the body pivot, required by the
# constant-scale equivalence. Retain the source cubes/UV byte for byte.
geo=json.loads((r/'references/client-elytra/vanilla-elytra.json').read_text())
assert all(b['pivot']==[0,24,0] for b in geo['bones'])
man=json.loads(pack['manifest.json']);man['header']['uuid']=str(uuid.uuid4());man['header']['name']='GeyserGlow LAB root-scale-free Elytra48'
for m in man['modules']:m['uuid']=str(uuid.uuid4())
pack['manifest.json']=json.dumps(man,separators=(',',':')).encode()
changed=[n for n in pack if pack[n]!=before.get(n)]
assert set(changed)=={new,path,'manifest.json'}
out.mkdir(parents=True);rp=out/'elytra-rootfree48.mcpack'
with zipfile.ZipFile(rp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n,v in sorted(pack.items()):z.writestr(n,v)
jar['geyser-cooldown-animation.mcpack']=rp.read_bytes()
assert jar['extension.yml'].count(b'version: 1.3.15-vv-lab.47')==1
jar['extension.yml']=jar['extension.yml'].replace(b'version: 1.3.15-vv-lab.47',b'version: 1.3.15-vv-lab.48')
j=out/'GeyserCooldownAnimation-1.3.15-vv-lab.48.jar'
with zipfile.ZipFile(j,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for n,v in sorted(jar.items()):z.writestr(n,v)
(out/'changes.json').write_text(json.dumps({'base':47,'changed':changed,'scale':1.067,'preserves':'Native rotations, cubes, UV and state controller; equivalent constant scale moved to wing transforms','visual_status':'not_tested'},indent=2)+'\n')
print(j)
