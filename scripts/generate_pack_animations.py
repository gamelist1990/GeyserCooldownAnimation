#!/usr/bin/env python3
"""Generate this project's authored, formula-based hand-lowering animations."""
import json
from pathlib import Path

# Visible lowering/recovery timings requested by the user, in seconds.
PROFILES = {
    "hand": 0.25,
    "sword": 0.65,
    "pickaxe": 0.90,
    "diamond_axe": 1.05,
    "iron_axe": 1.15,
    "stone_axe": 1.30,
    "mace": 1.65,
}
LOWER_TIME = 0.125
LOWER_DISTANCE = 20.0

def definitions():
    animations = {}
    for name, duration in PROFILES.items():
        # A triangular envelope: down quickly, then return steadily to neutral.
        # This is an independently authored expression, not imported keyframe JSON.
        expression = (
            f"query.is_first_person ? -{LOWER_DISTANCE:.1f} * "
            f"math.clamp(math.min(query.anim_time / {LOWER_TIME:.3f}, "
            f"({duration:.3f} - query.anim_time) / {duration - LOWER_TIME:.3f}), 0.0, 1.0) : 0.0"
        )
        animations["animation.geyser_cooldown." + name] = {
            "loop": False,
            "animation_length": duration,
            "bones": {"rightarm": {"position": [0.0, expression, 0.0]}},
        }
    return {"format_version": "1.8.0", "animations": animations}

if __name__ == "__main__":
    output = Path(__file__).resolve().parents[1] / "resource-pack/animations/cooldown.animation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(definitions(), indent=2) + "\n", encoding="utf-8")
    print(output)
