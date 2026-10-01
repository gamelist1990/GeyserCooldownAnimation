#!/usr/bin/env python3
"""Validate versioned JARs and the integrated resource pack, then package assets."""
import argparse
import hashlib
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?")
from validate_resource_pack import validate_archive as validate_pack


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    version = args.version
    if not VERSION.fullmatch(version):
        parser.error("Use a version such as 1.0.0 or 1.1.0-rc.1")
    sources = [
        (ROOT / "build/libs" / f"GeyserCooldownAnimation-{version}.jar", "extensions", "extension.yml"),
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
            for notice in ("META-INF/LICENSE",
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
    docs = ["README.md", "INSTALL.md", "LICENSE",
            "licenses/GeyserExtensionTemplate-MIT.txt",
            "resource-pack/README.md", "resource-pack/THIRD_PARTY_NOTICES.md"]
    release_notes = f"docs/releases/v{version}.md"
    if (ROOT / release_notes).is_file():
        docs.append(release_notes)
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
