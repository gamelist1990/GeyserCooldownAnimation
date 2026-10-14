#!/usr/bin/env python3
"""Build one explicit lab-only variation of a recorded baseline pack/JAR."""
import argparse
import copy
import io
import json
from pathlib import Path
import uuid
import zipfile


def build(source, output, variant):
    if output.exists():
        raise ValueError("Do not overwrite an existing experiment")
    with zipfile.ZipFile(source) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    with zipfile.ZipFile(io.BytesIO(entries['geyser-cooldown-animation.mcpack'])) as archive:
        pack = {name: archive.read(name) for name in archive.namelist()}
    baseline = pack.copy()
    material = json.loads(pack['materials/entity.material'])
    compact_report = {}
    if variant in ('compact-static-body-bones', 'compact-forward-items', 'compact-armor-color'):
        from compact_static_bones import compact
        animated = set()
        for path, data in pack.items():
            if not path.startswith('animations/') or not path.endswith('.json'):
                continue
            try:
                animations = json.loads(data).get('animations', {})
            except ValueError:
                import pyjson5
                animations = pyjson5.loads(data.decode()).get('animations', {})
            for animation in animations.values():
                animated.update(name.lower() for name in animation.get('bones', {}))
        for path in ('models/entity/player_outline.geo.json', 'models/entity/wide_player_outline.geo.json',
                     'models/entity/vv_body_mask_slim.geo.json', 'models/entity/vv_body_mask_wide.geo.json'):
            doc = json.loads(pack[path])
            for index, model in enumerate(doc['minecraft:geometry']):
                doc['minecraft:geometry'][index], report = compact(model, animated)
                compact_report[model['description']['identifier']] = report
            pack[path] = json.dumps(doc, separators=(',', ':')).encode()
    if variant == 'compact-armor-color':
        for path in ('render_controllers/vv_native_armor.render_controllers.json',
                     'render_controllers/vv_bound_helmet.render_controllers.json'):
            doc = json.loads(pack[path])
            for name, rc in doc['render_controllers'].items():
                if name.endswith('_outline_color') or name.endswith('_outline_black'):
                    rc['color'] = copy.deepcopy(rc['overlay_color'])
            pack[path] = json.dumps(doc, separators=(',', ':')).encode()
    if variant == 'mask-surface-clearance':
        for path in ('models/entity/vv_body_mask_slim.geo.json', 'models/entity/vv_body_mask_wide.geo.json'):
            doc = json.loads(pack[path])
            for geometry in doc['minecraft:geometry']:
                for bone in geometry['bones']:
                    for cube in bone.get('cubes', []):
                        cube['inflate'] = float(cube.get('inflate', 0)) + 0.03
            pack[path] = json.dumps(doc, separators=(',', ':')).encode()
    if variant == 'blend-preserving-mask':
        mask = material['materials']['vv_forward_mask:entity_alphablend']
        mask['+states'] = [state for state in mask['+states'] if state != 'DisableColorWrite']
        if 'Blending' not in mask['+states']:
            mask['+states'].append('Blending')
        mask['blendSrc'] = 'Zero'
        mask['blendDst'] = 'One'
    if variant in ('blend-preserving-mask', 'mask-surface-clearance', 'compact-static-body-bones', 'compact-forward-items', 'compact-armor-color'):
        path = 'render_controllers/armor/armor.render_controllers.json'
        controllers = json.loads(pack[path])
        rc = controllers['render_controllers']
        rc['controller.render.gca_glowing_armor'] = rc.pop('controller.render.armor')
        pack[path] = json.dumps(controllers, separators=(',', ':')).encode()
        count = 0
        for path in pack:
            if not path.startswith('attachables/') or not path.endswith('.json'):
                continue
            if b'controller.render.armor' not in pack[path]:
                continue
            pack[path] = pack[path].replace(b'controller.render.armor', b'controller.render.gca_glowing_armor')
            count += 1
        if count != 30:
            raise RuntimeError(f'Expected 30 private armor consumers, found {count}')
    if variant == 'visible-mask-diagnostic':
        mask = material['materials']['vv_forward_mask:entity_alphablend']
        mask['+states'] = [state for state in mask['+states'] if state != 'DisableColorWrite']
        path = 'render_controllers/player.render_controllers.json'
        controllers = json.loads(pack[path])
        mask_rc = controllers['render_controllers']['controller.render.vv_forward_mask']
        mask_rc['overlay_color'] = {'r': 0, 'g': 1, 'b': 0, 'a': 1}
        mask_rc['ignore_lighting'] = True
        pack[path] = json.dumps(controllers, separators=(',', ':')).encode()
    if variant == 'shared-body-pose':
        count = 0
        for path in pack:
            if not path.startswith('render_controllers/') or not path.endswith('.json'):
                continue
            try:
                controllers = json.loads(pack[path])
            except ValueError:
                continue
            changed_controller = False
            for name, rc in controllers.get('render_controllers', {}).items():
                if rc.get('geometry') in ('Geometry.outline_layer', 'Geometry.wide_outline_layer'):
                    rc['rebuild_animation_matrices'] = False
                    count += 1
                    changed_controller = True
            if changed_controller:
                pack[path] = json.dumps(controllers, separators=(',', ':')).encode()
        if count != 4:
            raise RuntimeError(f'Expected 4 body outline controllers, found {count}')
    if variant == 'double-sided-mask':
        mask = material['materials']['vv_forward_mask:entity_alphablend']
        mask['-states'] = [state for state in mask.get('-states', []) if state != 'DisableCulling']
        mask['+states'].append('DisableCulling')
    if variant == 'native-body-mask':
        path = 'render_controllers/player.render_controllers.json'
        controllers = json.loads(pack[path])
        rc = controllers['render_controllers']
        mask = copy.deepcopy(rc['controller.render.player.third_person'])
        mask['materials'] = [{'*': 'Material.vv_forward_mask'}]
        for key in ('overlay_color', 'is_hurt_color', 'on_fire_color'):
            mask.pop(key, None)
        rc['controller.render.vv_forward_mask'] = mask
        pack[path] = json.dumps(controllers, separators=(',', ':')).encode()
    if variant in ('forward-held-items', 'armor-union-mask', 'compact-forward-items'):
        for alias, parent in [('vv_item_clean', 'entity_alphatest'),
                              ('vv_item_clean_glint', 'entity_alphatest_glint')]:
            item = material['materials'].pop(f'{alias}:{parent}')
            item['+defines'] = ['ALPHA_TEST']
            if alias.endswith('_glint'):
                item['+defines'].append('GLINT')
                item['+samplerStates'] = [{'samplerIndex': 1, 'textureWrap': 'Repeat'}]
            material['materials'][f'{alias}:entity_alphablend'] = item
    if variant == 'armor-union-mask':
        path = 'entity/player.entity.json'
        player = json.loads(pack[path])
        description = player['minecraft:client_entity']['description']
        slots = {'helmet': 'head', 'chestplate': 'chest', 'leggings': 'legs', 'boots': 'feet'}
        count = 0
        for entry in description['render_controllers']:
            if not isinstance(entry, dict): continue
            for name in list(entry):
                prefix = 'controller.render.vv_armor_mask_'
                suffix = '_layer_customization'
                if not name.startswith(prefix) or not name.endswith(suffix): continue
                item = name[len(prefix):-len(suffix)]
                slot = next((slot for kind, slot in slots.items() if item.endswith('_' + kind)), None)
                if slot is None: continue
                entry[name] = ("!variable.is_first_person && !variable.map_face_icon && !query.is_spectator"
                    " && q.property('glow:color') > 0 && q.property('glow:a') > 0"
                    f" && q.is_item_name_any('slot.armor.{slot}', 0, 'minecraft:{item}')")
                count += 1
        if count != 29: raise RuntimeError(f'Expected 29 union masks, found {count}')
        description['textures']['vv_union_coverage_1'] = 'textures/entity/vv_native_coverage_1'
        description['textures']['vv_union_coverage_2'] = 'textures/entity/vv_native_coverage_2'
        pack[path] = json.dumps(player, separators=(',', ':')).encode()
        path = 'render_controllers/vv_armor_masks.render_controllers.json'
        controllers = json.loads(pack[path])
        for name, rc in controllers['render_controllers'].items():
            rc['textures'] = ['Texture.vv_union_coverage_2' if '_leggings_' in name else 'Texture.vv_union_coverage_1']
        pack[path] = json.dumps(controllers, separators=(',', ':')).encode()
        # Full vanilla-sized cubes plus real armor UV alpha coverage. Shortening
        # an inflated sleeve/boot cube scales its UV differently and can erase
        # the bare hand or create a gap while rotating.
        path = 'models/entity/vv_armor_masks.geo.json'
        geometry = json.loads(pack[path])
        for model in geometry['minecraft:geometry']:
            slot = model['description']['identifier'].removeprefix('geometry.vv_armor_mask_')
            model['description'].update(texture_width=64, texture_height=32)
            for bone in model['bones']:
                if bone['name'] == 'hat':
                    bone.pop('cubes', None)
                for cube in bone.get('cubes', []):
                    if bone['name'] == 'head':
                        cube.update(origin=[-4,24,-4], size=[8,8,8], inflate=1, uv=[0,0])
                    elif bone['name'] == 'body':
                        cube.update(origin=[-4,12,-2], size=[8,12,4],
                                    inflate=1.01 if slot == 'chestplate' else .5, uv=[16,16])
                    elif bone['name'] in ('leftArm', 'rightArm'):
                        cube['origin'][1] = 12
                        cube['size'][1] = 12
                        cube.update(inflate=1, uv=[40,16])
                    elif bone['name'] in ('leftLeg', 'rightLeg'):
                        cube['origin'][1] = 0
                        cube['size'][1] = 12
                        cube.update(inflate=1 if slot == 'boots' else .5, uv=[0,16])
        pack[path] = json.dumps(geometry, separators=(',', ':')).encode()
    pack['materials/entity.material'] = json.dumps(material, separators=(',', ':')).encode()
    manifest = json.loads(pack['manifest.json'])
    manifest['header']['uuid'] = str(uuid.uuid4())
    manifest['header']['name'] = 'Glowing LAB ' + variant
    for module in manifest['modules']:
        module['uuid'] = str(uuid.uuid4())
    pack['manifest.json'] = json.dumps(manifest, separators=(',', ':')).encode()
    changed = [name for name in baseline if baseline[name] != pack[name]]
    allowed = {'manifest.json', 'materials/entity.material'}
    if variant == 'compact-armor-color':
        allowed.update({'render_controllers/vv_native_armor.render_controllers.json', 'render_controllers/vv_bound_helmet.render_controllers.json'})
    if variant in ('compact-static-body-bones', 'compact-forward-items', 'compact-armor-color'):
        allowed.update({'models/entity/player_outline.geo.json', 'models/entity/wide_player_outline.geo.json',
                        'models/entity/vv_body_mask_slim.geo.json', 'models/entity/vv_body_mask_wide.geo.json'})
    if variant == 'mask-surface-clearance':
        allowed.update({'models/entity/vv_body_mask_slim.geo.json', 'models/entity/vv_body_mask_wide.geo.json'})
    if variant in ('blend-preserving-mask', 'mask-surface-clearance', 'compact-static-body-bones', 'compact-forward-items', 'compact-armor-color'):
        allowed.add('render_controllers/armor/armor.render_controllers.json')
        allowed.update(name for name in pack if name.startswith('attachables/') and name.endswith('.json'))
    if variant == 'shared-body-pose':
        allowed.update({'render_controllers/slim/outline_player.render_controllers.json',
                        'render_controllers/wide/outline_wide_player.render_controllers.json'})
    if variant in ('native-body-mask', 'visible-mask-diagnostic'):
        allowed.add('render_controllers/player.render_controllers.json')
    if variant == 'armor-union-mask':
        allowed.update({'entity/player.entity.json', 'models/entity/vv_armor_masks.geo.json',
                        'render_controllers/vv_armor_masks.render_controllers.json'})
    if not set(changed) <= allowed:
        raise RuntimeError('Unexpected baseline modification')
    output.mkdir(parents=True)
    pack_path = output / f'{variant}.mcpack'
    with zipfile.ZipFile(pack_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(pack.items()):
            archive.writestr(name, data)
    entries['geyser-cooldown-animation.mcpack'] = pack_path.read_bytes()
    number = {'double-sided-mask': 18, 'native-body-mask': 19, 'forward-held-items': 20, 'armor-union-mask': 21, 'shared-body-pose': 22, 'visible-mask-diagnostic': 23, 'blend-preserving-mask': 24, 'mask-surface-clearance': 25, 'compact-static-body-bones': 26, 'compact-forward-items': 27, 'compact-armor-color': 28}[variant]
    entries['extension.yml'] = entries['extension.yml'].replace(
        b'version: 1.3.15-vv-prototype.17', f'version: 1.3.15-vv-lab.{number}'.encode())
    jar_path = output / f'GeyserCooldownAnimation-1.3.15-vv-lab.{number}.jar'
    with zipfile.ZipFile(jar_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(entries.items()):
            archive.writestr(name, data)
    (output / 'changes.json').write_text(json.dumps(dict(variant=variant, changed=changed,
        source=str(source), compact=compact_report, experimental=True), indent=2) + '\n')
    print(jar_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--variant', choices=['double-sided-mask', 'native-body-mask', 'forward-held-items', 'armor-union-mask', 'shared-body-pose', 'visible-mask-diagnostic', 'blend-preserving-mask', 'mask-surface-clearance', 'compact-static-body-bones', 'compact-forward-items', 'compact-armor-color'], required=True)
    args = parser.parse_args()
    build(args.source, args.output, args.variant)
