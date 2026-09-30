#!/usr/bin/env python3
"""Validate versioned JARs and the project's MIT resource pack, then package assets."""
import argparse
import hashlib
import io
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?")
PROFILES = {"hand", "sword", "pickaxe", "diamond_axe", "iron_axe", "stone_axe", "mace"}

def validate_pack(data, version):
    with zipfile.ZipFile(io.BytesIO(data)) as pack:
        expected = {"manifest.json", "animations/cooldown.animation.json", "README.md", "LICENSE"}
        actual = {name for name in pack.namelist() if not name.endswith("/")}
        if actual != expected:
            raise SystemExit("Unexpected resource pack content")
        manifest = json.loads(pack.read("manifest.json"))
        numeric = [int(part) for part in version.split("-", 1)[0].split(".")]
        if manifest["header"]["version"] != numeric:
            raise SystemExit("Resource pack version mismatch")
        if manifest["modules"][0]["version"] != numeric or manifest["metadata"]["license"] != "MIT":
            raise SystemExit("Resource pack metadata mismatch")
        definitions = json.loads(pack.read("animations/cooldown.animation.json"))["animations"]
        if set(definitions) != {"animation.geyser_cooldown." + profile for profile in PROFILES}:
            raise SystemExit("Resource pack animation namespace mismatch")
        if any(animation["loop"] is not False or animation["animation_length"] <= 0
               for animation in definitions.values()):
            raise SystemExit("Invalid animation duration or loop")
        if pack.read("LICENSE") != (ROOT / "LICENSE").read_bytes():
            raise SystemExit("Resource pack license mismatch")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    version = args.version
    if not VERSION.fullmatch(version):
        parser.error("Use a version such as 1.0.0 or 1.1.0-rc.1")
    sources = [
        (ROOT / "build/libs" / f"GeyserCooldownAnimation-{version}.jar", "extensions", "extension.yml"),
        (ROOT / "paper-bridge/build/libs" / f"GeyserCooldownPaperBridge-{version}.jar", "plugins", "plugin.yml"),
    ]
    pack_path = ROOT / "build/resource-pack" / f"GeyserCooldownAnimation-pack-{version}.mcpack"
    if not pack_path.is_file():
        raise SystemExit(f"Resource pack output missing: {pack_path}")
    pack_data = pack_path.read_bytes()
    validate_pack(pack_data, version)
    for source, folder, descriptor in sources:
        if not source.is_file():
            raise SystemExit(f"Build output missing: {source}")
        with zipfile.ZipFile(source) as jar:
            metadata = jar.read(descriptor).decode()
            entry_version = re.search(r"^version:\s*(.+?)\s*$", metadata, re.MULTILINE)
            if not entry_version or entry_version.group(1).strip("'\"") != version:
                raise SystemExit(f"Descriptor version mismatch: {source.name}")
            main_class = re.search(r"^main:\s*(.+?)\s*$", metadata, re.MULTILINE)
            if not main_class or main_class.group(1).replace(".", "/") + ".class" not in jar.namelist():
                raise SystemExit(f"Entrypoint class missing: {source.name}")
            packed_assets = {name for name in jar.namelist() if name.endswith((".mcpack", ".mcaddon"))}
            expected_assets = {"geyser-cooldown-animation.mcpack"} if folder == "extensions" else set()
            if packed_assets != expected_assets:
                raise SystemExit(f"Unexpected embedded resource pack: {source.name}")
            if folder == "extensions" and jar.read("geyser-cooldown-animation.mcpack") != pack_data:
                raise SystemExit("Embedded resource pack differs from release resource pack")
            for notice in ("META-INF/LICENSE", "META-INF/THIRD_PARTY_NOTICES.md",
                           "META-INF/licenses/GeyserExtensionTemplate-MIT.txt"):
                if notice not in jar.namelist():
                    raise SystemExit(f"License notice missing: {source.name}: {notice}")

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    artifacts = []
    for source in [*(source for source, _, _ in sources), pack_path]:
        target = dist / source.name
        shutil.copyfile(source, target)
        artifacts.append(target)
    bundle = dist / f"GeyserCooldownAnimation-{version}.zip"
    docs = ["README.md", "INSTALL.md", "LICENSE", "THIRD_PARTY_NOTICES.md",
            "licenses/GeyserExtensionTemplate-MIT.txt"]
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        for source, folder, _ in sources:
            archive.write(source, f"{folder}/{source.name}")
        archive.write(pack_path, f"packs/{pack_path.name}")
        for name in docs:
            archive.write(ROOT / name, name)
    artifacts.append(bundle)
    checksum = dist / "SHA256SUMS.txt"
    checksum.write_text("".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
        for path in artifacts), encoding="utf-8")
    for path in [*artifacts, checksum]:
        print(path.relative_to(ROOT))

if __name__ == "__main__":
    main()
