#!/usr/bin/env python3
"""Run repeatable inputs/equipment on the local Geyser lab and record video.

No automatic visual PASS is asserted. Captures and timing are review evidence.
Only the localhost lab RCON endpoint is accepted by the companion client.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import zipfile

from control import GameWindow
from rcon import Rcon


ARMOR_SLOTS = ("head", "chest", "legs", "feet")
ARMOR_ITEMS = ("helmet", "chestplate", "leggings", "boots")


class RecordedRcon(Rcon):
    def __init__(self, server_dir):
        super().__init__(server_dir)
        self.responses = []

    def command(self, command):
        response = super().command(command)
        self.responses.append({"command": command, "response": response})
        errors = ("Unknown or incomplete command", "Incorrect argument", "No entity was found",
                  "No player was found", "That position is not loaded", "Unknown item")
        if any(error in response for error in errors):
            raise RuntimeError(f"Lab command failed: {command}: {response}")
        return response


def equip(rcon, armor, main, off, target="@a"):
    if isinstance(armor, dict) and set(armor) - set(ARMOR_SLOTS):
        raise ValueError("Unknown armor slot in case")
    for slot, suffix in zip(ARMOR_SLOTS, ARMOR_ITEMS):
        item = armor.get(slot, "air") if isinstance(armor, dict) else (
            "air" if armor == "none" else f"{armor}_{suffix}")
        if not re.fullmatch(r"[a-z0-9_]+", item):
            raise ValueError("Unsafe armor item")
        rcon.command(f"item replace entity {target} armor.{slot} with minecraft:{item}")
    for slot, item in (("mainhand", main), ("offhand", off)):
        rcon.command(f"item replace entity {target} weapon.{slot} with minecraft:{item}")


def run(server_dir, plan, output, actor="self", fps=30, capture_width=1280):
    if output.exists():
        raise ValueError("Use a new output directory for each run")
    steps = json.loads(plan.read_text())
    if not isinstance(steps, list) or not steps:
        raise ValueError("Case plan must be a nonempty array")
    if fps not in (15, 30, 60) or capture_width not in (960, 1280, 1920):
        raise ValueError("Unsupported capture settings")
    output.mkdir(parents=True)
    rcon = RecordedRcon(server_dir)
    game = GameWindow()
    fixture = None
    fixture_log = None
    target = "VisualProbe" if actor == "probe" else "@a"
    record = {"started": datetime.now(timezone.utc).isoformat(),
        "plan_sha256": hashlib.sha256(plan.read_bytes()).hexdigest(),
        "visual_status": "review_required", "cases": []}
    record["actor"] = actor
    record["capture"] = {"fps": fps, "width": capture_width}
    pack = server_dir / "plugins/Geyser-Spigot/extensions/geyser-cooldown-animation/geyser-cooldown-animation.mcpack"
    record["served_pack_sha256"] = hashlib.sha256(pack.read_bytes()).hexdigest()
    try:
        players = rcon.command("list")
        if "There are 1 " not in players:
            raise RuntimeError("Lab must have exactly one connected visual-test player")
        if actor == "probe":
            skin_extension = server_dir / 'plugins/Geyser-Spigot/extensions/VisualLabSkin-0.1.0.jar'
            server_log = server_dir / 'logs/latest.log'
            log_offset = server_log.stat().st_size
            if skin_extension.exists():
                with zipfile.ZipFile(skin_extension) as archive:
                    shape = archive.read('fixture.shape').decode().strip() if 'fixture.shape' in archive.namelist() else 'wide'
                    record['fixture_skin'] = {'shape': shape,
                        'sha256': hashlib.sha256(archive.read('fixture.rgba')).hexdigest(),
                        'applied_event_verified': False}
            else:
                record['fixture_skin'] = {'shape': 'not_pinned', 'applied_event_verified': False}
            fixture_log = open(output / "fixture.log", "w")
            fixture = subprocess.Popen([sys.executable, str(Path(__file__).with_name("run_probe.py")),
                "--server-dir", str(server_dir), "--output", str(server_dir.parent / "bot")],
                stdin=subprocess.PIPE, text=True, stdout=fixture_log, stderr=fixture_log)
            deadline = time.monotonic() + 35
            while time.monotonic() < deadline:
                if fixture.poll() is not None:
                    raise RuntimeError("Fixed player failed to start; inspect fixture.log")
                players = rcon.command("list")
                if "There are 2 " in players and "VisualProbe" in players:
                    break
                time.sleep(1)
            else:
                raise RuntimeError("Fixed player did not join the lab")
            rcon.command("tp @a[name=!VisualProbe] 0 60 -4 0 0")
            rcon.command("effect clear @a[name=!VisualProbe] minecraft:glowing")
            # Let client-side spawn/teleport interpolation settle before the
            # first baseline; a transient model at the camera is not a test.
            time.sleep(3)
            if skin_extension.exists():
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    with server_log.open('rb') as log:
                        log.seek(log_offset)
                        applied = f'Applied fixed {shape} lab skin to VisualProbe'.encode() in log.read()
                    if applied:
                        record['fixture_skin']['applied_event_verified'] = True
                        break
                    time.sleep(.5)
                else:
                    raise RuntimeError('Fixed skin application was not confirmed in this run')
        rcon.command("team add visual_lab")
        rcon.command("team modify visual_lab color light_purple")
        rcon.command(f"team join visual_lab {target}")
        rcon.command("team modify visual_lab nametagVisibility never")
        rcon.command("weather clear 999999")
        game.focus()
        for case in steps:
            label = case["name"]
            if not re.fullmatch(r"[a-z0-9_-]+", label):
                raise ValueError("Unsafe case label")
            game.release()
            if fixture:
                # The client can enter its idle overlay while only the remote
                # fixture moves. Ctrl alone does not move the observer.
                game.tap('Control_L')
            team_color = case.get("team_color", "light_purple")
            supported_colors = ("black", "dark_blue", "dark_green", "dark_aqua", "dark_red",
                "dark_purple", "gold", "gray", "dark_gray", "blue", "green", "aqua",
                "red", "light_purple", "yellow", "white")
            if team_color not in supported_colors:
                raise ValueError("Unsupported lab team color")
            rcon.command(f"team modify visual_lab color {team_color}")
            rcon.command("time set noon")
            occlusion = case.get("occlusion", "none")
            if occlusion not in ("none", "wall", "full_wall", "entity"):
                raise ValueError("Unknown lab occlusion fixture")
            rcon.command("fill -2 60 -2 2 63 -2 air")
            rcon.command("execute if entity @e[tag=visual_lab_occluder] run kill @e[tag=visual_lab_occluder]")
            if occlusion == "wall":
                rcon.command("fill -2 60 -2 2 60 -2 oak_planks")
            elif occlusion == "full_wall":
                rcon.command("fill -2 60 -2 2 63 -2 oak_planks")
            elif occlusion == "entity":
                rcon.command('summon minecraft:cow 0 60 -2 {Tags:["visual_lab_occluder"],NoAI:1b,Silent:1b,DeathLootTable:"minecraft:empty"}')
            if fixture:
                fixture.stdin.write("move 0 0\nshift false\njump false\n"); fixture.stdin.flush()
            rcon.command(f"tp {target} 0 60 0 180 0")
            equip(rcon, case.get("armor", "none"), case.get("main", "air"), case.get("off", "air"), target)
            rcon.command(f"effect clear {target} minecraft:glowing")
            if case.get("glow", True):
                rcon.command(f"effect give {target} minecraft:glowing 99999 0 true")
            time.sleep(2 if occlusion == "entity" else 1)
            if fixture:
                fixture.stdin.write(f"bounds {float(case.get('motion_bounds', 0))}\n")
                fixture.stdin.flush()
            geometry = game.window.get_geometry()
            video = output / f"{label}.mp4"
            recorder = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "x11grab",
                "-window_id", str(game.window.id), "-framerate", str(fps), "-i", os.environ["DISPLAY"],
                "-vf", f"scale={capture_width}:-2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-y", str(video)], stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            events = []
            started = time.monotonic()
            try:
                repeat = case.get("repeat", 1)
                if not isinstance(repeat, int) or not 1 <= repeat <= 120:
                    raise ValueError("Case repeat must be 1–120")
                actions = case.get("actions", [{"hold": [], "seconds": 2}])
                for action in actions * repeat:
                    duration = float(action.get("seconds", 1))
                    if not 0 <= duration <= 10:
                        raise ValueError("Each action must be at most 10 seconds")
                    if "yaw" in action or "pitch" in action:
                        if fixture:
                            fixture.stdin.write(f"pose {float(action.get('yaw',180))} {float(action.get('pitch',0))}\n")
                            fixture.stdin.flush()
                        else:
                            rcon.command(f"tp {target} 0 60 0 {float(action.get('yaw',180))} {float(action.get('pitch',0))}")
                    keys = action.get("hold", [])
                    events.append({"t": time.monotonic() - started, "action": action})
                    if fixture:
                        speed = 0.065 if 'Shift_L' in keys else 0.215
                        dx = speed * (("a" in keys) - ("d" in keys))
                        dz = speed * (("s" in keys) - ("w" in keys))
                        fixture.stdin.write(f"move {dx} {dz}\nshift {str('Shift_L' in keys).lower()}\njump {str('space' in keys).lower()}\n")
                        fixture.stdin.flush()
                    else:
                        for key in keys:game.key(key)
                    time.sleep(duration)
                    if fixture:
                        fixture.stdin.write("move 0 0\nshift false\njump false\n"); fixture.stdin.flush()
                    else:
                        for key in keys:game.key(key, False)
            finally:
                game.release()
                _, stderr = recorder.communicate(b"q\n", timeout=20)
                (output / f"{label}.ffmpeg.log").write_bytes(stderr)
            game.capture(output / f"{label}.png")
            if recorder.returncode:
                raise RuntimeError(f"Recording failed for {label}")
            record["cases"].append({"name": label, "conditions": case,
                "seconds": time.monotonic() - started, "events": events,
                "video": video.name, "window": [geometry.width, geometry.height],
                "visual_status": "review_required"})
            record["commands"] = rcon.responses
            (output / "run.json").write_text(json.dumps(record, indent=2) + "\n")
            print(f"Captured {label}", flush=True)
    finally:
        game.release()
        try:
            rcon.command("fill -2 60 -2 2 63 -2 air")
            rcon.command("execute if entity @e[tag=visual_lab_occluder] run kill @e[tag=visual_lab_occluder]")
        except (OSError, RuntimeError):
            pass
        if fixture:
            try:
                fixture.communicate("quit\n", timeout=15)
            except (subprocess.TimeoutExpired, BrokenPipeError):
                if fixture.poll() is None:
                    fixture.terminate()
                    try:
                        fixture.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        fixture.kill()
                        fixture.wait(timeout=5)
        if fixture_log:
            fixture_log.close()
        rcon.close()
        record["commands"] = rcon.responses
        (output / "run.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server-dir", type=Path, required=True)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--actor", choices=["self", "probe"], default="self",
        help="Probe requires an in-game first-person observer view of the fixed player")
    p.add_argument("--fps", type=int, choices=[15, 30, 60], default=30)
    p.add_argument("--capture-width", type=int, choices=[960, 1280, 1920], default=1280)
    args = p.parse_args()
    run(args.server_dir, args.plan, args.output, args.actor, args.fps, args.capture_width)
