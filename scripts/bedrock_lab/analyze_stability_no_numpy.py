#!/usr/bin/env python3
"""Review-only magenta outline stability metrics from existing stationary recordings."""
import json,subprocess,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/"build/bedrock-lab"
VIDEOS=[
("candidate36-native-regression-v1","iron_full"),
("candidate36-native-regression-v1","diamond_full"),
("candidate36-seven-colors-v1","iron_no_shield_on"),
("candidate37-elytra-six-angles-v1","elytra_back_glow"),
("candidate38-elytra-six-angles-v1","elytra_back_glow"),
]
def analyze(video):
    x,y,w,h=510,220,250,300
    ff=["ffmpeg","-hide_banner","-loglevel","error","-i",str(video),"-vf",f"crop={w}:{h}:{x}:{y},fps=12","-pix_fmt","rgb24","-f","rawvideo","pipe:1"]
    p=subprocess.Popen(ff,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    rows=[]
    size=w*h*3
    while True:
        dat=p.stdout.read(size)
        if not dat:break
        if len(dat)!=size:raise ValueError("Truncated RGB frame")
        count=0
        for i in range(0,size,3):
            r,g,b=dat[i],dat[i+1],dat[i+2]
            if r>95 and b>100 and r>g*1.4 and b>g*1.4:count+=1
        rows.append(count)
    _,err=p.communicate(timeout=20)
    if p.returncode:raise RuntimeError(err.decode(errors="replace"))
    assert len(rows)>=12,(video,len(rows))
    return dict(file=str(video),fps_sample=12,roi=[x,y,x+w,y+h],frames=len(rows),
                min=min(rows),max=max(rows),median=statistics.median(rows),
                mean=round(statistics.mean(rows),2),std=round(statistics.pstdev(rows),2),
                empty_frames=sum(n<10 for n in rows),counts=rows,
                note="Review aid only; body movement/pose and ffmpeg sampling affect counts")
results=[]
for directory,stem in VIDEOS:
    path=ROOT/"runs"/directory/(stem+".mp4")
    if not path.exists():print("MISSING",path);continue
    entry=analyze(path);results.append(entry)
    print(directory,stem,"range",entry["min"],entry["max"],"mean",entry["mean"],"std",entry["std"],"zeros",entry["empty_frames"])
out=ROOT/"variants/elytra-balanced39/flicker-source-metrics.json"
out.write_text(json.dumps(results,indent=2)+"\n")
print("SAVED",out)
