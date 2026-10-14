#!/usr/bin/env python3
"""Sample only the Minecraft window and save live color changes for review.

Run with the bundled NumPy/Pillow Python. Counts are not correctness scores:
armor, skin and lights can have the same color as an outline.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np
from PIL import Image
from control import GameWindow


def monitor(output, seconds, fps):
    if output.exists():
        raise ValueError('Use a new output directory')
    if not 1 <= seconds <= 600 or not 1 <= fps <= 15:
        raise ValueError('Duration must be 1–600 seconds; FPS must be 1–15')
    game = GameWindow()
    output.mkdir(parents=True)
    geometry = game.window.get_geometry()
    width = 960
    height = round(geometry.height * width / geometry.width / 2) * 2
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'x11grab',
        '-window_id', str(game.window.id), '-framerate', str(fps), '-i', os.environ['DISPLAY'],
        '-t', str(seconds), '-vf', f'scale={width}:{height}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    started = time.monotonic()
    best = {'magenta_pixels': -1, 'white_pixels': -1, 'changed_pixels': -1}
    previous = None
    count = 0
    with open(output / 'capture.log', 'wb') as log, open(output / 'samples.jsonl', 'w') as rows:
        capture = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=log)
        try:
            while True:
                remaining = width * height * 3
                chunks = []
                while remaining:
                    data = capture.stdout.read(remaining)
                    if not data:
                        break
                    chunks.append(data)
                    remaining -= len(data)
                if remaining:
                    if chunks:
                        raise RuntimeError('Incomplete capture frame')
                    break
                frame = np.frombuffer(b''.join(chunks), np.uint8).reshape(height, width, 3)
                crop = frame[height//4:height*9//10, width//4:width*3//4].astype(np.int16)
                r, g, b = crop[:,:,0], crop[:,:,1], crop[:,:,2]
                values = {
                    'magenta_pixels': int(((r>90)&(b>90)&(r>g*1.45)&(b>g*1.45)).sum()),
                    'white_pixels': int(((crop.min(2)>210)&(crop.max(2)-crop.min(2)<35)).sum()),
                    'changed_pixels': 0 if previous is None else int((np.abs(crop-previous).max(2)>30).sum())}
                row = dict(frame=count, seconds=count/fps, wall_seconds=round(time.monotonic()-started,3), **values)
                rows.write(json.dumps(row)+'\n'); rows.flush()
                for metric, value in values.items():
                    if value > best[metric]:
                        best[metric] = value
                        Image.fromarray(frame).save(output / f'peak-{metric}.png')
                if count % fps == 0:
                    print(json.dumps(row), flush=True)
                previous = crop
                count += 1
            capture.wait(timeout=15)
            if capture.returncode or not count:
                raise RuntimeError('Live capture failed; inspect capture.log')
        finally:
            if capture.poll() is None:
                capture.terminate(); capture.wait(timeout=15)
    (output / 'summary.json').write_text(json.dumps(dict(
        frames=count, fps=fps, maxima=best, visual_status='review_required',
        roi=[width//4,height//4,width*3//4,height*9//10]), indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=60)
    parser.add_argument('--fps', type=int, default=5)
    args = parser.parse_args()
    monitor(args.output, args.seconds, args.fps)
