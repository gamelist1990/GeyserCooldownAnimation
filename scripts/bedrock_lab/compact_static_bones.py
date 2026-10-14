"""Collapse only unanimated identity-transform bones, preserving every cube."""
import copy
import json
from collections import Counter


PLAYER_BONES = set('root waist body head hat cape jacket leftArm rightArm leftLeg rightLeg '
                   'leftItem rightItem leftSleeve rightSleeve leftPants rightPants helmet '
                   'bodyArmor leftArmArmor rightArmArmor leftLegging rightLegging '
                   'leftBoot rightBoot leftSock rightSock belt'.lower().split())


def compact(model, animated_names):
    bones = model['bones']
    by_name = {bone['name']: bone for bone in bones}
    if len(by_name) != len(bones):
        raise ValueError('Duplicate bones cannot be compacted safely')
    keep = set()
    for bone in bones:
        rotation = bone.get('rotation', [0,0,0])
        identity = all(isinstance(v, (int,float)) and v == 0 for v in rotation)
        simple = set(bone) <= {'name','parent','pivot','cubes','rotation'}
        if (not bone.get('parent') or bone['name'].lower() in PLAYER_BONES | animated_names
                or not identity or not simple):
            keep.add(bone['name'])

    def owner(name):
        visited = set()
        while name not in keep:
            if name in visited or name not in by_name:
                raise ValueError('Invalid bone hierarchy')
            visited.add(name)
            name = by_name[name]['parent']
        return name

    result = copy.deepcopy(model)
    retained = {}
    for bone in bones:
        if bone['name'] not in keep:
            continue
        out = copy.deepcopy(bone)
        if 'parent' in out:
            out['parent'] = owner(out['parent'])
        out.pop('cubes', None)
        retained[out['name']] = out
    before = Counter()
    for bone in bones:
        destination = owner(bone['name'])
        for cube in bone.get('cubes', []):
            retained[destination].setdefault('cubes', []).append(copy.deepcopy(cube))
            before[(destination, json.dumps(cube, sort_keys=True))] += 1
    result['bones'] = list(retained.values())
    after = Counter((bone['name'], json.dumps(cube, sort_keys=True))
                    for bone in result['bones'] for cube in bone.get('cubes', []))
    if before != after:
        raise RuntimeError('Cube geometry/UV data changed')
    # Only identity ancestors were removed; retain every pivot and rotation of
    # the remaining chain. No cube, UV, inflate, or rotation value is rewritten.
    for bone in result['bones']:
        original = by_name[bone['name']]
        for key in set(original) - {'parent','cubes'}:
            if original[key] != bone[key]:
                raise RuntimeError('Retained bone transform changed')
    return result, {'before_bones':len(bones), 'after_bones':len(result['bones']),
                    'cubes':sum(before.values()), 'cube_data_preserved':True}
