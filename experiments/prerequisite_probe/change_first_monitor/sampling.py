"""Goal-blind, causal temporal proposal and shared evidence selection."""
import cv2
import numpy as np


def sample(frames, times_ms, max_full=8, max_candidates=3):
    if len(frames) != len(times_ms) or not frames:
        raise ValueError('frame/time mismatch')
    gray = [cv2.resize(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY), (64, 48)).astype(np.int16) for f in frames]
    edges = []
    stable_indices=[]
    camera_uncertain=False
    for i in range(1, len(gray)):
        a, b = gray[i-1], gray[i]
        raw=float(np.mean(np.abs(b-a)))
        if raw>8:
            shift,response=cv2.phaseCorrelate(a.astype(np.float32),b.astype(np.float32))
            if np.hypot(*shift)>1.5 and response>.55:
                warp=np.float32([[1,0,-shift[0]],[0,1,-shift[1]]])
                registered=cv2.warpAffine(b.astype(np.float32),warp,(64,48),flags=cv2.INTER_LINEAR)
                valid=cv2.warpAffine(np.ones((48,64),np.uint8),warp,(64,48))>0
                aligned=float(np.mean(np.abs(registered[valid]-a[valid]))) if np.any(valid) else raw
                if aligned<raw*.45:
                    camera_uncertain=True
                    b=registered.astype(np.int16)
        # Remove global brightness drift; spatially coherent displacement survives.
        diff = np.abs((b-a) - np.median(b-a))
        mask = (diff > 18).astype(np.uint8)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        components = [stats[k] for k in range(1, n) if stats[k, cv2.CC_STAT_AREA] >= 3]
        best = max(components, key=lambda x: x[cv2.CC_STAT_AREA], default=None)
        score = int(best[cv2.CC_STAT_AREA]) if best is not None else 0
        if times_ms[i]-times_ms[i-1]>=500 and score<4:
            stable_indices.append(i)
        if score:
            h,w=frames[i].shape[:2]
            x,y,bw,bh=[int(v) for v in best[:4]]
            bbox=[int(x*w/64),int(y*h/48),int((x+bw)*w/64),int((y+bh)*h/48)]
            edges.append({'before_index': i-1, 'after_index': i, 'score': score,'bbox_xyxy':bbox})
    # A structure can move only a little while the arm dominates every adjacent-frame
    # difference. Compare the two endpoint states before ranking transient motion.
    persistent = None
    if len(gray) >= 3 and not camera_uncertain:
        endpoint_delta = gray[-1] - gray[0]
        endpoint_mask = (np.abs(endpoint_delta - np.median(endpoint_delta)) > 18).astype(np.uint8)
        count, _, stats, _ = cv2.connectedComponentsWithStats(endpoint_mask, 8)
        parts = sorted((stats[k] for k in range(1, count) if stats[k, cv2.CC_STAT_AREA] >= 4),
                       key=lambda part: -part[cv2.CC_STAT_AREA])
        if parts:
            keep = [parts[0]]
            if len(parts) > 1 and parts[1][cv2.CC_STAT_AREA] >= .35 * parts[0][cv2.CC_STAT_AREA]:
                left = min(int(part[cv2.CC_STAT_LEFT]) for part in parts[:2])
                top = min(int(part[cv2.CC_STAT_TOP]) for part in parts[:2])
                right = max(int(part[cv2.CC_STAT_LEFT] + part[cv2.CC_STAT_WIDTH]) for part in parts[:2])
                bottom = max(int(part[cv2.CC_STAT_TOP] + part[cv2.CC_STAT_HEIGHT]) for part in parts[:2])
                if (right-left) * (bottom-top) <= .35 * 64 * 48:
                    keep = parts[:2]
            left = min(int(part[cv2.CC_STAT_LEFT]) for part in keep)
            top = min(int(part[cv2.CC_STAT_TOP]) for part in keep)
            right = max(int(part[cv2.CC_STAT_LEFT] + part[cv2.CC_STAT_WIDTH]) for part in keep)
            bottom = max(int(part[cv2.CC_STAT_TOP] + part[cv2.CC_STAT_HEIGHT]) for part in keep)
            h, w = frames[-1].shape[:2]
            persistent = {'before_index': 0, 'after_index': len(frames)-1,
                          'score': sum(int(part[cv2.CC_STAT_AREA]) for part in keep),
                          'bbox_xyxy': [int(left*w/64), int(top*h/48), int(right*w/64), int(bottom*h/48)],
                          'stable_before_index': 0, 'stable_after_index': len(frames)-1}
    # Temporal diversity prevents a large robot motion from monopolizing proposals.
    chosen = []
    for e in sorted(edges, key=lambda x: (-x['score'], x['after_index'])):
        if all(abs(e['after_index'] - q['after_index']) > 1 for q in chosen):
            chosen.append(e)
        if len(chosen) == max_candidates - int(persistent is not None):
            break
    for e in chosen:
        before=[j for j in stable_indices if j<=e['before_index'] and e['before_index']-j<=2]
        after=[j for j in stable_indices if j>=e['after_index'] and j-e['after_index']<=2]
        e['stable_before_index']=max(before) if before else None
        e['stable_after_index']=min(after) if after else None
    episodes=0; last_edge=-10
    for e in edges:
        if e['after_index']-last_edge>1:episodes+=1
        last_edge=e['after_index']
    # Reserve broad coverage before allocating scarce slots to high-motion peaks.
    reserve=min(len(frames),max_full,min(6,max_full))
    selected=set(np.linspace(0,len(frames)-1,reserve,dtype=int).tolist())
    selected.update((0,len(frames)-1))
    for e in chosen:
        for i in (e['after_index'],e['before_index']):
            if len(selected)>=max_full:break
            selected.add(i)
    selected=sorted(selected)
    candidates = ([persistent] if persistent else []) + sorted(chosen, key=lambda x: x['after_index'])
    return {'selected_indices': selected, 'candidates': candidates,
            'overflow': episodes > max_candidates, 'times_ms': [times_ms[i] for i in selected],
            'stable_indices':stable_indices,'camera_uncertain':camera_uncertain}
