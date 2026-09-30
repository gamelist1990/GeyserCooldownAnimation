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
def cooldown_animation(duration):
    # Server packets only update timing metadata. The local controller owns
    # the visible recovery and waits for Bedrock's swing to finish.
    return {
        "animation_length": 0.05,
        "timeline": {"0.0": [
            f"variable.gca_duration = {duration:.6f};",
            "variable.gca_requested_at = query.life_time;",
            "variable.gca_requested = 1;",
        ]},
    }


def definitions():
    animations = {
        "animation.player." + name: cooldown_animation(duration)
        for name, duration in PROFILES.items()
    }
    animations.update({
        f"animation.player.cooldown_tick_{ticks}": cooldown_animation(ticks / 20)
        for ticks in range(1, 201)
    })
    return {"format_version": "1.8.0", "animations": animations}


def render_document(document):
    return (
        "// mc-disable resourcepack.model.bone.missing\n"
        "// rightArm belongs to the built-in player geometry.humanoid.custom.\n"
        + json.dumps(document, indent=2) + "\n"
    )


def rendered():
    return render_document(definitions())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the generated file is stale")
    args = parser.parse_args()
    pack = Path(__file__).resolve().parents[1] / "resource-pack/animations"
    outputs = {
        pack / "cooldown.animation.json": rendered(),
    }
    for output, content in outputs.items():
        if args.check:
            if not output.is_file() or output.read_text(encoding="utf-8") != content:
                raise SystemExit(f"{output.name} is stale; run python scripts/generate_pack_animations.py")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content, encoding="utf-8")
        print(output)



if __name__ == "__main__":
    main()
