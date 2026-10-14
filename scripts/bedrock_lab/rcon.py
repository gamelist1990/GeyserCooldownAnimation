#!/usr/bin/env python3
"""Local lab RCON only; passwords are read from ignored owner-only config."""
import argparse
from pathlib import Path
import socket
import struct


class Rcon:
    def __init__(self, server_dir):
        props = dict(line.split("=", 1) for line in (Path(server_dir) / "server.properties").read_text().splitlines()
                     if "=" in line and not line.startswith("#"))
        if props.get("server-ip") != "127.0.0.1" or props.get("rcon.port") != "25573":
            raise ValueError("Refusing non-lab RCON endpoint")
        self.socket = socket.create_connection(("127.0.0.1", 25573), timeout=10)
        self.sequence = 0
        self.send(3, props["rcon.password"])
        while True:
            sequence, kind, text = self.receive()
            if sequence == -1:
                raise RuntimeError("Lab RCON authentication failed")
            if kind == 2:
                break

    def exact(self, length):
        data = b""
        while len(data) < length:
            part = self.socket.recv(length - len(data))
            if not part:
                raise EOFError("Lab RCON closed")
            data += part
        return data

    def send(self, kind, text):
        self.sequence += 1
        body = struct.pack("<ii", self.sequence, kind) + text.encode() + b"\0\0"
        self.socket.sendall(struct.pack("<i", len(body)) + body)
        return self.sequence

    def receive(self):
        length = struct.unpack("<i", self.exact(4))[0]
        if not 10 <= length <= 1048576:
            raise ValueError("Invalid RCON packet")
        body = self.exact(length)
        sequence, kind = struct.unpack("<ii", body[:8])
        return sequence, kind, body[8:-2].decode(errors="replace")

    def command(self, text):
        sequence = self.send(2, text)
        while True:
            reply, kind, response = self.receive()
            if reply == sequence:
                return response

    def close(self):
        self.socket.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server-dir", type=Path, required=True)
    p.add_argument("commands", nargs="+")
    args = p.parse_args()
    r = Rcon(args.server_dir)
    try:
        for command in args.commands:
            print(r.command(command))
    finally:
        r.close()
