#!/usr/bin/env python3
"""Check Crossplay swing wiring and all server-duration recovery variants."""
import json
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


for ticks in range(1, 201):
    animation = definitions()["animations"][f"animation.player.cooldown_tick_{ticks}"]
    assert not animation.get("bones")
    assert animation["animation_length"] == 0.05
    assert f"variable.gca_duration = {ticks / 20:.6f};" in animation["timeline"]["0.0"]

recovery = json.loads((ROOT / "resource-pack/animations/recovery.animation.json").read_text())["animations"]
controllers = json.loads((ROOT / "resource-pack/animation_controllers/player.animation_controllers.json").read_text())["animation_controllers"]
states = controllers["controller.animation.geyser_cooldown.recovery"]["states"]
for kind, depth in [("sword",10),("axe",12),("mace",12)]:
    animation = recovery["animation.geyser_cooldown.recovery_"+kind]
    frames = animation["bones"]["rightArm"]["position"]
    start = frames["0.0"]
    end = frames["1.0"]
    assert (start["post"] if isinstance(start,dict) else start) == [0,-depth,0]
    assert (end["post"] if isinstance(end,dict) else end) == [0,0,0]
    if kind != "mace":
        assert start["lerp_mode"] == end["lerp_mode"] == "catmullrom"
    else:
        assert isinstance(start,list)
    assert "query.delta_time / math.max(variable.gca_active_duration, 0.05)" in animation["anim_time_update"]
    assert states[kind]["transitions"][0] == {"waiting":"variable.attack_time > 0"}
    assert "variable.gca_duration - (query.life_time - variable.gca_requested_at)" in states[kind]["on_entry"][1]
    target = next(v for transition in states["waiting"]["transitions"] for k,v in transition.items() if k==kind)
    assert target.startswith("variable.attack_time <= 0")
    assert not states["waiting"].get("animations")

# Exercise timing: signal during swing remains visually silent; remaining
# recovery completes at the server deadline; new swings interrupt recovery.
for duration in [ticks/20 for ticks in range(1,201)]:
    for swing_end in (0.1,0.3,0.5):
        active_duration = max(0.05, duration-swing_end)
        finish = swing_end+active_duration
        assert finish >= swing_end+0.05-1e-10
        assert abs(finish-max(duration,swing_end+0.05)) < 1e-10

print("PASS: 200 timing-only signals; recovery waits for swings; depths/interpolation and restart transitions.")
