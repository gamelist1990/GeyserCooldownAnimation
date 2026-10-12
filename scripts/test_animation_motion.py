#!/usr/bin/env python3
"""Check Crossplay swing wiring and all server-duration recovery variants."""
import json
import re
from types import SimpleNamespace
from pathlib import Path
from generate_pack_animations import definitions

ROOT = Path(__file__).resolve().parents[1]
document = json.loads((ROOT / "resource-pack/animations/weapon_swing.animation.json").read_text())
animations = document["animations"]
prefix = "animation.player.first_person.attack_rotation_custom_"
assert set(animations) == {prefix + name for name in ("sword", "axe", "mace")}
assert animations[prefix + "sword"]["animation_length"] == 0.5
assert animations[prefix + "axe"]["animation_length"] == 0.5
assert animations[prefix + "mace"]["animation_length"] == 0.7
assert all(set(a["bones"]) == {"rightArm"} for a in animations.values())
geometry = json.loads((ROOT / "resource-pack/models/entity/item_first_person.json").read_text())
assert len(geometry["minecraft:geometry"][0]["bones"]) == 1
assert geometry["minecraft:geometry"][0]["bones"][0]["texture_meshes"]

# The reference's rightitem geometry uses legacy bone-name attachment and
# authored offsets. Adding slot binding changes that coordinate frame and
# moves the sword high above the hand. Native spear/trident models below use
# their own binding-based transforms and must retain their bindings.
for model in ("item_first_person", "item_third_person", "item_third_person_axe"):
    document = json.loads((ROOT / f"resource-pack/models/entity/{model}.json").read_text())
    bone = document["minecraft:geometry"][0]["bones"][0]
    assert bone["name"] == "rightitem"
    assert "binding" not in bone
    assert bone["pivot"] == [0, 0, 0]
    if model == "item_first_person":
        mesh = bone["texture_meshes"][0]
        assert mesh["local_pivot"] == [9, 0, 6]
        assert mesh["position"] == [2.01, -0.5, -1]
        assert mesh["rotation"] == [0, -135, 90]


for ticks in range(1, 501):
    animation = definitions()["animations"][f"animation.player.cooldown_20ms_{ticks}"]
    assert not animation.get("bones")
    assert animation["animation_length"] == 0.02
    assert f"variable.gca_duration = {ticks / 50:.6f};" in animation["timeline"]["0.0"]

recovery = json.loads((ROOT / "resource-pack/animations/recovery.animation.json").read_text())["animations"]
controllers = json.loads((ROOT / "resource-pack/animation_controllers/player.animation_controllers.json").read_text())["animation_controllers"]
states = controllers["controller.animation.geyser_cooldown.recovery"]["states"]
for kind, depth in [("sword",10),("axe",12),("mace",12),("tool",10)]:
    animation = recovery["animation.geyser_cooldown.recovery_"+("sword" if kind == "tool" else kind)]
    frames = animation["bones"]["rightArm"]["position"]
    start = frames["0.0"]
    end = frames["1.0"]
    assert (start["post"] if isinstance(start,dict) else start) == [0,-depth,0]
    assert (end["post"] if isinstance(end,dict) else end) == [0,0,0]
    if kind != "mace":
        assert start["lerp_mode"] == end["lerp_mode"] == "catmullrom"
    else:
        assert isinstance(start,list)
    assert "query.delta_time / math.max(variable.gca_active_duration, 0.02)" in animation["anim_time_update"]
    assert states[kind]["transitions"][2] == {"waiting":"variable.attack_time > 0"}
    assert "variable.gca_duration - (query.life_time - variable.gca_requested_at)" in states[kind]["on_entry"][1]
    target = next(v for transition in states["waiting"]["transitions"] for k,v in transition.items() if k==kind)
    assert target.startswith("variable.attack_time <= 0")
    assert not states["waiting"].get("animations")

# Evaluate the pack's actual Molang conditions and motion expressions with
# representative equipment, timing, attack, and use states.
player = json.loads((ROOT / "resource-pack/entity/player.entity.json").read_text())["minecraft:client_entity"]["description"]
class Query:
    def __init__(self, item, tags, elapsed=0, using=False):
        self.item, self.tags, self.life_time, self.is_using_item = item, tags, elapsed, using
    def is_item_equipped(self, slot):
        assert slot == "main_hand"
        return bool(self.item)
    def equipped_item_any_tag(self, slot, *tags):
        assert slot == "slot.weapon.mainhand"
        return any(tag.removeprefix("minecraft:is_") in self.tags for tag in tags)
    def is_item_name_any(self, slot, *names):
        assert slot == "slot.weapon.mainhand"
        return self.item in names
math = SimpleNamespace(max=max, min=min, clamp=lambda x, lo, hi: min(hi, max(lo, x)))
def evaluate(expression, query, variable):
    expression = expression.replace("&&", " and ").replace("||", " or ")
    expression = re.sub(r"!(?!=)", " not ", expression).strip()
    return eval(expression, {"__builtins__": {}}, {"query": query, "variable": variable, "math": math})
def equipment(item, tags, elapsed=0, using=False):
    query = Query(item, tags, elapsed, using)
    variable = SimpleNamespace(gca_duration=1, gca_requested_at=0, gca_requested=1,
                               attack_time=0.5, is_first_person=True, is_using_vr=False)
    for line in player["scripts"]["pre_animation"]:
        if line.startswith("variable.gca_") and not line.startswith(("variable.gca_elapsed", "variable.gca_lower_duration", "variable.gca_lower_amount")):
            name, expression = line.rstrip(";").split(" = ", 1)
            setattr(variable, name.removeprefix("variable."), evaluate(expression, query, variable))
    update_motion(query, variable)
    return query, variable

def update_motion(query, variable):
    for line in player["scripts"]["pre_animation"]:
        if line.startswith(("variable.gca_elapsed =", "variable.gca_lower_duration =", "variable.gca_lower_amount =")):
            name, expression = line.rstrip(";").split(" = ", 1)
            setattr(variable, name.removeprefix("variable."), evaluate(expression, query, variable))
fixtures = [("", set(), "hand"), ("minecraft:trident", {"trident"}, "trident"),
            ("minecraft:mace", set(), "mace")]
for material in ("wooden", "stone", "copper", "iron", "golden", "diamond", "netherite"):
    for suffix, kind in [("pickaxe", "tool"), ("shovel", "tool"), ("spear", "spear"), ("sword", "sword"), ("axe", "axe")]:
        fixtures.append((f"minecraft:{material}_{suffix}", {suffix}, kind))
for item, tags, kind in fixtures:
    query, variable = equipment(item, tags)
    selected = [name for name in ("hand", "tool", "spear", "trident", "sword", "axe", "mace") if getattr(variable, "gca_"+name)]
    assert selected == [kind], (item, selected)
    if kind == "spear":
        # Drawing is owned by vanilla's swap-item animation. Even repeated
        # attack signals cannot enter custom lowering with a spear equipped.
        for elapsed in (0,0.01,0.25,1):
            query.life_time = elapsed
            assert not evaluate(states["idle"]["transitions"][0]["waiting"],query,variable)
            assert evaluate(states["waiting"]["transitions"][0]["idle"],query,variable)
        assert "spear" not in states
        assert "gca_recovery_spear" not in player["animations"]
        assert player["animations"]["first_person_swap_item"] == "animation.player.first_person.swap_item"
        continue
    assert evaluate(states["idle"]["transitions"][0]["waiting"], query, variable)
    # New categories enter during the normal swing, including a 250ms bare-hand cooldown.
    variable.attack_time = 0 if kind in ("sword", "axe", "mace", "tool") else 0.5
    target = next(name for t in states["waiting"]["transitions"] for name, condition in t.items() if evaluate(condition, query, variable))
    assert target == kind, (item, target)
    assert player["animations"]["gca_recovery_"+kind] in recovery
    # A fresh signal on equipment change must survive the previous state's exit.
    other = "mace" if kind != "mace" else "hand"
    assert evaluate(states[other]["transitions"][0]["waiting"], query, variable)
    query.life_time = 1.01
    assert evaluate(states[kind]["transitions"][1]["idle"], query, variable)
    assert evaluate(states["waiting"]["transitions"][0]["idle"], query, variable)
for kind, depth in [("hand",20),("trident",20)]:
    animation = recovery["animation.geyser_cooldown.recovery_"+("sword" if kind == "tool" else kind)]
    assert animation["loop"]
    expression = animation["bones"]["rightArm"]["position"][1]
    for ticks in range(1,501):
        query, variable = equipment("", set())
        variable.gca_duration = ticks/50
        for fraction in (0,0.25,0.5,0.75,1,1.5):
            query.life_time = variable.gca_duration*fraction
            update_motion(query,variable)
            lower_time = min(0.125, variable.gca_duration/2)
            elapsed = query.life_time
            expected = elapsed/lower_time if elapsed <= lower_time else max(0,(variable.gca_duration-elapsed)/(variable.gca_duration-lower_time))
            assert abs(evaluate(expression,query,variable) + depth*expected) < 1e-9
        query.life_time = min(0.125,variable.gca_duration/2)
        update_motion(query,variable)
        assert evaluate(expression,query,variable) == -depth
        # A new signal uses its own timestamp without adding another arm displacement.
        query.life_time = variable.gca_requested_at = 5
        update_motion(query,variable)
        assert evaluate(expression,query,variable) == 0
        query.life_time += min(0.125,variable.gca_duration/2)
        update_motion(query,variable)
        assert abs(evaluate(expression,query,variable) + depth) < 1e-9
    for first_person, vr, using in [(False,False,False),(True,True,False),(True,False,True)]:
        query, variable = equipment("", set(), using=using)
        variable.is_first_person, variable.is_using_vr = first_person, vr
        assert not evaluate(states[kind]["animations"][0]["gca_recovery_"+kind],query,variable)
for item, tags in [("minecraft:bow", {"bow"}), ("minecraft:iron_hoe", {"hoe"}), ("minecraft:apple", set())]:
    query, variable = equipment(item,tags)
    assert not evaluate(states["idle"]["transitions"][0]["waiting"], query, variable)
# Trident uses the vanilla swing; spear remains with the vanilla spear controller.
attack = controllers["controller.animation.player.first_person_attack"]["states"]["default"]["animations"]
for kind, item, tags in [("trident","minecraft:trident",{"trident"}), ("spear","minecraft:iron_spear",{"spear"})]:
    query, variable = equipment(item,tags)
    active = [name for entry in attack for name, condition in entry.items() if evaluate(condition,query,variable)]
    assert active == (["first_person_attack_rotation"] if kind == "trident" else [])
# Every shovel/pickaxe material selects only the sword swing, and recovers
# with the same pose after the swing using its own server duration.
for item,tags,kind in fixtures:
    if kind != "tool": continue
    query,variable = equipment(item,tags)
    selected = [name for entry in attack for name,condition in entry.items() if evaluate(condition,query,variable)]
    assert selected == ["attack_rotation_custom_sword"], (item,selected)
    assert states["tool"]["animations"] == states["sword"]["animations"]
    variable.attack_time = 0.5
    assert not any("tool" in t and evaluate(t["tool"],query,variable) for t in states["waiting"]["transitions"])
print("PASS: equipment routing; 500 cooldown durations; short bare-hand cooldown during swings; expiry, repeated signals, native spear/trident swing, and use/view guards.")

# Native slot bindings and spear/trident use poses must accompany attachables.
for kind, bone in [("spear","spear"),("trident","pole")]:
    geometry = json.loads((ROOT / f"resource-pack/models/entity/{kind}.geo.json").read_text())["minecraft:geometry"][0]
    assert geometry["bones"][0]["name"] == bone
    assert geometry["bones"][0]["binding"] == "q.item_slot_to_bone_name(c.item_slot)"
trident = json.loads((ROOT / "resource-pack/attachables/misc/trident.json").read_text())["minecraft:attachable"]["description"]
assert "wield_first_person_raise" in trident["animations"]
assert "wield_first_person_riptide" in trident["animations"]
for material in ("wooden", "stone", "copper", "iron", "golden", "diamond", "netherite"):
    spear = json.loads((ROOT / f"resource-pack/attachables/spear/{material}_spear.json").read_text())["minecraft:attachable"]["description"]
    assert spear["geometry"]["default"] == "geometry.geyser_cooldown.spear"
    assert "hit_controller" in spear["scripts"]["animate"]
print("PASS: native spear/trident slot bindings, charge/riptide/hit animation wiring; all material attachables.")
