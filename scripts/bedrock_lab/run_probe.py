#!/usr/bin/env python3
"""Compile/start the fixed Java player on the dedicated local visual lab."""
import argparse
import os
from pathlib import Path
import subprocess
from rcon import Rcon


def start(server, output):
    if not (server / 'lab.json').is_file():
        raise ValueError('Expected the isolated lab metadata')
    client = Rcon(server)  # Validates the dedicated localhost RCON endpoint.
    try:
        print(client.command('whitelist add VisualProbe'), flush=True)
    finally:
        client.close()
    source = Path(__file__).with_name('VisualProbe.java').resolve()
    output.mkdir(parents=True, exist_ok=True)
    libraries = [server / 'plugins/Geyser-Spigot.jar', *sorted(server.glob('libraries/**/*.jar'))]
    classpath = os.pathsep.join(str(path.resolve()) for path in libraries)
    subprocess.run(['javac', '-cp', classpath, '-d', str(output), str(source)], check=True)
    classpath += os.pathsep + str(output.resolve())
    os.execvp('java', ['java', '-Xms32M', '-Xmx160M', '-cp', classpath, 'VisualProbe'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    start(args.server_dir, args.output)
