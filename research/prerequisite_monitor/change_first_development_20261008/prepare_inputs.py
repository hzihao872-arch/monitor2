"""Private-side conversion from a source clip to an anonymous, fixed RGB prefix."""
import argparse
import json
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from experiments.prerequisite_probe.change_first_monitor.prefix import materialize_frames


def prepare_video(video, as_of_ms, out):
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise ValueError('cannot open source video')
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps<=0:raise ValueError('invalid source fps')
    frames = [];times=[]
    i = 0
    step=max(1,round(fps/2))
    while round(i * 1000 / fps) <= as_of_ms:
        ok, bgr = cap.read()
        if not ok:
            break
        if i%step==0:
            frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            times.append(round(i*1000/fps))
        i += 1
    cap.release()
    last_decoded_ms=round((i-1)*1000/fps)
    if not frames or as_of_ms-last_decoded_ms>1000/fps+1:
        raise ValueError('source has no frame at requested cutoff')
    return materialize_frames(frames, as_of_ms, out, fps=min(fps,2),times_ms=times)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--video', required=True)
    p.add_argument('--as-of-ms', type=int, required=True)
    p.add_argument('--output', required=True)
    a=p.parse_args()
    print(json.dumps(prepare_video(a.video,a.as_of_ms,a.output)))
