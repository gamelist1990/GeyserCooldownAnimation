#!/usr/bin/env python3
"""Create an isolated visual lab from existing server binaries.

No production configs, worlds, or services are modified. RCON credentials stay
in the ignored lab directory with owner-only permissions and are never printed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import shutil

import yaml


def prepare(source, destination, candidate, bedrock_address, player):
    if destination.exists():
        raise ValueError("Lab directory already exists; do not overwrite an existing world")
    if not candidate.is_file():
        raise ValueError("Candidate JAR is missing")
    paper = sorted(source.glob("paper-*.jar"))[-1]
    destination.mkdir(parents=True, mode=0o700)
    shutil.copy2(paper, destination / "paper.jar")
    for folder in ("cache", "libraries", "versions"):
        if (source / folder).is_dir():
            shutil.copytree(source / folder, destination / folder)
    if (source / "eula.txt").read_text().strip() != "eula=true":
        raise ValueError("Existing server does not have an accepted EULA")
    shutil.copy2(source / "eula.txt", destination / "eula.txt")
    # Floodgate identities differ from offline Java UUIDs for the same name.
    identities = [entry for entry in json.loads((source / "whitelist.json").read_text())
                  if entry.get("name", "").lstrip(".") == player.lstrip(".")]
    if len(identities) != 1:
        raise ValueError("Expected one existing whitelist identity for the lab player")
    (destination / "whitelist.json").write_text(json.dumps(identities, indent=2) + "\n")
    plugins = destination / "plugins"
    extension_dir = plugins / "Geyser-Spigot/extensions"
    extension_dir.mkdir(parents=True)
    for name in ("Geyser-Spigot.jar", "floodgate-spigot.jar"):
        shutil.copy2(source / "plugins" / name, plugins / name)
    shutil.copy2(candidate, extension_dir / candidate.name)
    shutil.copy2(source / "plugins/Geyser-Spigot/extensions/GeyserJavaGlowing-0.2.13.jar",
                 extension_dir / "GeyserJavaGlowing-0.2.13.jar")
    floodgate = plugins / "floodgate"
    floodgate.mkdir()
    for name in ("key.pem", "config.yml"):
        shutil.copy2(source / "plugins/floodgate" / name, floodgate / name)
        (floodgate / name).chmod(0o600)
    config = yaml.safe_load((source / "plugins/Geyser-Spigot/config.yml").read_text())
    config["bedrock"].update(address=bedrock_address, port=19142, transport="nethernet", **{"webrtc-port": 0})
    config["bedrock"]["signaling"] = {"mode": "builtin", "builtin": {
        "advertise-addresses": [f"{bedrock_address}:19142"]}}
    config["saved-user-logins"] = []
    config["log-player-ip-addresses"] = False
    config["gameplay"]["server-name"] = "Glowing visual lab"
    config["gameplay"]["force-resource-packs"] = True
    config["advanced"]["resource-pack-urls"] = []
    config["advanced"]["bedrock"]["broadcast-port"] = 19142
    config["advanced"]["bedrock"]["use-haproxy-protocol"] = False
    config["advanced"]["java"]["use-haproxy-protocol"] = False
    (plugins / "Geyser-Spigot/config.yml").write_text(yaml.safe_dump(config, sort_keys=False))
    password = secrets.token_hex(24)
    properties = {
        "server-ip": "127.0.0.1", "server-port": 25572, "online-mode": "false",
        "enable-rcon": "true", "rcon.port": 25573, "rcon.password": password,
        "broadcast-rcon-to-ops": "false", "max-players": 2, "gamemode": "creative",
        "difficulty": "peaceful", "view-distance": 2, "simulation-distance": 2,
        "white-list": "true", "enforce-whitelist": "true",
        "level-name": "glowing_lab", "level-type": "minecraft:flat",
        "generator-settings": json.dumps({"biome": "minecraft:plains", "layers": [
            {"block": "minecraft:bedrock", "height": 1},
            {"block": "minecraft:gray_concrete", "height": 59}]}, separators=(",", ":")),
        "generate-structures": "false", "spawn-protection": 0, "motd": "Glowing visual lab",
        "enable-query": "false", "allow-flight": "true", "enforce-secure-profile": "false"}
    prop = destination / "server.properties"
    prop.write_text("\n".join(f"{key}={value}" for key, value in properties.items()) + "\n")
    prop.chmod(0o600)
    metadata = {"created": datetime.now(timezone.utc).isoformat(), "candidate": candidate.name,
        "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        "java_port": 25572, "bedrock_port": 19142, "rcon_port": 25573,
        "production_modified": False}
    (destination / "lab.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--destination", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--bedrock-address", required=True, help="Local LAN interface address; NetherNet rejects loopback")
    p.add_argument("--player", required=True, help="Existing whitelisted Bedrock player to permit in the lab")
    args = p.parse_args()
    prepare(args.source, args.destination, args.candidate, args.bedrock_address, args.player)
