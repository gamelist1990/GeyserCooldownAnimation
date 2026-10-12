#!/usr/bin/env python3
"""Generate timing-only signals for server cooldowns in 20 ms steps."""
import argparse
import json
from pathlib import Path

STEP_MILLIS = 20
MAX_STEPS = 10_000 // STEP_MILLIS
def cooldown_animation(duration):
    # Server packets only update timing metadata. The local controller owns
    # the visible recovery, including the swing wait for swords/axes/maces.
    return {
        "animation_length": STEP_MILLIS / 1000,
        "timeline": {"0.0": [
            f"variable.gca_duration = {duration:.6f};",
            "variable.gca_requested_at = query.life_time;",
            "variable.gca_requested = 1;",
        ]},
    }


def definitions():
    animations = {
        f"animation.player.cooldown_20ms_{ticks}": cooldown_animation(ticks * STEP_MILLIS / 1000)
        for ticks in range(1, MAX_STEPS + 1)
    }
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
