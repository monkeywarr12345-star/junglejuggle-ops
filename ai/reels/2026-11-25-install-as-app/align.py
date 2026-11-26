import numpy as np, wave, json
from scipy.signal import stft
def load(p):
    w = wave.open(p); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; w.close()
    if sr != 16000:
        from scipy.signal import resample_poly
        from math import gcd
        g = gcd(sr, 16000); x = resample_poly(x, 16000 // g, sr // g)
    return x
HOP = 160  # 10ms
def feat(x):
    f, t, Z = stft(x, 16000, nperseg=512, noverlap=512 - HOP)
    S = np.abs(Z) ** 2
    # mel-ish log bands
    edges = np.geomspace(80, 7600, 41); fb = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (f >= a) & (f < b); fb.append(S[m].sum(0) if m.any() else np.zeros(S.shape[1]))
    M = np.log(np.array(fb) + 1e-8)
    M = M - M.mean(1, keepdims=True)
    M = M / (np.linalg.norm(M, axis=0, keepdims=True) + 1e-6)
    return M.T
A = feat(load('vold/v_fit_old.wav')); B = feat(load('v_fit_new.wav'))
n, m = len(A), len(B)
C = 1 - A @ B.T  # cosine distance
# banded DTW
band = 400
INF = 1e18
D = np.full((n + 1, m + 1), INF); D[0, 0] = 0
P = np.zeros((n + 1, m + 1), np.int8)
for i in range(1, n + 1):
    c = int(i * m / n); lo = max(1, c - band); hi = min(m, c + band)
    for j in range(lo, hi + 1):
        d = C[i - 1, j - 1]
        a, b, cc = D[i - 1, j - 1], D[i - 1, j], D[i, j - 1]
        if a <= b and a <= cc: D[i, j] = a + d; P[i, j] = 0
        elif b <= cc: D[i, j] = b + d; P[i, j] = 1
        else: D[i, j] = cc + d; P[i, j] = 2
i, j = n, m; path = []
while i > 0 and j > 0:
    path.append((i - 1, j - 1)); p = P[i, j]
    if p == 0: i -= 1; j -= 1
    elif p == 1: i -= 1
    else: j -= 1
path = path[::-1]
pa = np.array(path)
# monotone map old frame -> mean new frame
mp = {}
for a, b in path: mp.setdefault(a, []).append(b)
xs = np.array(sorted(mp)); ys = np.array([np.mean(mp[k]) for k in xs])
json.dump({'old': (xs * 0.01).round(3).tolist(), 'new': (ys * 0.01).round(3).tolist(), 'dur_old': n * 0.01, 'dur_new': m * 0.01}, open('align.json', 'w'))
print('frames', n, m, 'avg cost', D[n, m] / len(path))
