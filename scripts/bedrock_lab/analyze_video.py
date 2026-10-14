#!/usr/bin/env python3
"""Measure outline-color changes and export frames for manual visual review.

Requires NumPy and Pillow. White pixels can be armor or lighting: these metrics
are review aids, never a visual pass/fail oracle. Use a magenta team color and
a neutral background to separate bare-player outlines from skin colors.
"""
import argparse
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw


def analyze(video, destination):
    info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate", "-of", "json", str(video)]))["streams"][0]
    width, height = info["width"], info["height"]
    numerator, denominator = map(int, info["avg_frame_rate"].split("/"))
    fps = numerator / denominator
    destination.mkdir(parents=True, exist_ok=True)
    x0, y0, x1, y1 = width // 4, height // 4, width * 3 // 4, height * 9 // 10
    decoder = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-f", "rawvideo",
        "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    metrics, samples, best = [], [], {}
    size = width * height * 3
    index = 0
    while True:
        data = decoder.stdout.read(size)
        if not data:
            break
        if len(data) != size:
            raise RuntimeError("Incomplete decoded frame")
        frame = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)
        crop = frame[y0:y1, x0:x1].astype(np.int16)
        r, g, b = crop[:, :, 0], crop[:, :, 1], crop[:, :, 2]
        magenta = (r > 90) & (b > 90) & (r > g * 1.45) & (b > g * 1.45)
        white = (crop.min(axis=2) > 210) & (crop.max(axis=2) - crop.min(axis=2) < 35)
        row = {"frame": index, "seconds": round(index / fps, 4),
               "magenta_pixels": int(magenta.sum()), "white_pixels": int(white.sum()),
               "magenta_max_row_pixels": int(magenta.sum(axis=1).max())}
        metrics.append(row)
        for color in ("magenta", "white"):
            count = row[f"{color}_pixels"]
            if color not in best or count > best[color][0]:
                best[color] = (count, index, frame[y0:y1, x0:x1].copy())
        if index % max(1, round(fps / 3)) == 0:
            samples.append((index, frame[y0:y1, x0:x1].copy()))
        index += 1
    _, stderr = decoder.communicate(timeout=20)
    if decoder.returncode:
        raise RuntimeError(stderr.decode(errors="replace"))
    if not metrics:
        raise RuntimeError("Video contains no frames")
    for color, (_, frame_index, crop) in best.items():
        Image.fromarray(crop).save(destination / f"{video.stem}-max-{color}.png")
    selected = samples[::max(1, len(samples) // 12)][:12]
    cw, ch = x1 - x0, y1 - y0
    sheet = Image.new("RGB", (cw * 4, (ch + 25) * 3), "#202020")
    draw = ImageDraw.Draw(sheet)
    for tile, (frame_index, crop) in enumerate(selected):
        tx, ty = tile % 4 * cw, tile // 4 * (ch + 25)
        sheet.paste(Image.fromarray(crop), (tx, ty + 25))
        draw.text((tx + 4, ty + 4), f"frame {frame_index}, {frame_index/fps:.2f}s", fill="white")
    sheet.save(destination / f"{video.stem}-frames.jpg")
    report = {"video": video.name, "frames": index, "fps": fps, "roi": [x0,y0,x1,y1],
              "visual_status": "review_required", "metrics": metrics,
              "maxima": {color: {"pixels": count, "frame": frame_index}
                         for color, (count, frame_index, _) in best.items()}}
    (destination / f"{video.stem}-metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"video": video.name, "frames": index, "maxima": report["maxima"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for video in args.video:
        analyze(video, args.output)
