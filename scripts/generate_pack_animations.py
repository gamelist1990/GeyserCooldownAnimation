#!/usr/bin/env python3
"""Generate this project's authored, formula-based hand-lowering animations."""
import argparse
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
        animations["animation.player." + name] = {
            "loop": "hold_on_last_frame",
            "animation_length": duration,
            "loop_delay": "0",
            "bones": {
                "rightArm": {
                    "position": {
                        "0.0": [0, 0, 0],
                        f"{LOWER_TIME:.3f}": [0, f"variable.is_first_person && !query.equipped_item_any_tag('slot.weapon.mainhand', 'minecraft:is_pickaxe', 'minecraft:is_hoe') ? -{LOWER_DISTANCE:.0f} : 0", 0],
                        f"{duration:.2f}": [0, 0, 0],
                    }
                }
            },
        }
    return {"format_version": "1.8.0", "animations": animations}

def rendered():
    return (
        "// mc-disable resourcepack.model.bone.missing\n"
        "// rightArm belongs to the built-in player geometry.humanoid.custom.\n"
        + json.dumps(definitions(), indent=2) + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the generated file is stale")
    args = parser.parse_args()
    output = Path(__file__).resolve().parents[1] / "resource-pack/animations/cooldown.animation.json"
    content = rendered()
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != content:
            raise SystemExit("Cooldown animations are stale; run python scripts/generate_pack_animations.py")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
