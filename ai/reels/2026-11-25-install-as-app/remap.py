import json, re, subprocess, numpy as np
a = json.load(open('align.json'))
f0 = lambda t: float(np.interp(t, a['old'], a['new']))
def onsets(p):
    e = subprocess.run(['ffmpeg', '-nostdin', '-i', p, '-af', 'silencedetect=noise=-38dB:d=0.12', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', e)]
OLD = onsets('vold/v_fit_old.wav'); NEW = onsets('v_fit_new.wav')
DO, DN = OLD[-1], NEW[-1]  # file ends
anc = [(0.0, 0.0)]
for o in OLD[:-1]:
    p = f0(o); n = min(NEW[:-1], key=lambda q: abs(q - p))
    if abs(n - p) < 0.2 and n > anc[-1][1] + 0.05 and o > anc[-1][0] + 0.05: anc.append((o, n))
anc.append((DO, DN))
ao, an = zip(*anc)
F = lambda t: round(float(np.interp(t, ao, an)), 3)
print('anchors', len(anc), [(round(x, 2), round(y, 2)) for x, y in anc])
T = json.load(open('ov/tl_old.json'))
Dn = round(DN + 0.1, 2)
for c in T['caps']:
    c[0] = F(c[0]) if c[0] > 0 else 0
    if len(c) > 3 and c[3] is not None: c[3] = F(c[3])
for s in T['scenes']:
    s['t0'] = F(s['t0']); s['t1'] = F(s['t1'])
T['scenes'][-1]['t1'] = Dn
for k, v in T['ev'].items():
    if v: T['ev'][k] = F(v)
T['pops'] = [F(x) for x in [0.5, 6.0, 10.2, 10.7]]
T['dur'] = Dn
json.dump(T, open('ov/tl.json', 'w'), ensure_ascii=False)
S = json.load(open('bgseg_old.json'))
for s in S:
    s[0] = F(s[0]); s[1] = F(s[1])
    if s[2] == 'bgloop': s[3] = s[0]
S[-1][1] = Dn
json.dump(S, open('bgseg.json', 'w'))
print('dur', Dn)
