import numpy as np, wave
SR = 48000; D = 44.5
y = np.zeros(int(SR * (D + 1)))
rng = np.random.default_rng(7)
def add(t, s, g):
    i = int(t * SR); n = min(len(s), len(y) - i)
    if i >= 0 and n > 0: y[i:i + n] += s[:n] * g
def pop():
    n = int(SR * .12); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(900 * np.exp(-t * 30) + 300) / SR) * np.exp(-t * 35)
def boing():
    n = int(SR * .35); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(180 + 120 * np.sin(t * 40) * np.exp(-t * 6)) / SR) * np.exp(-t * 9) * .9
def swish():
    n = int(SR * .28); t = np.arange(n) / SR; w = rng.standard_normal(n)
    from numpy.fft import rfft, irfft
    f = rfft(w); fr = np.fft.rfftfreq(n, 1 / SR); f[(fr < 900) | (fr > 6000)] = 0
    return irfft(f, n) * np.sin(np.pi * t / t[-1]) ** 2 * 1.4
def thump():
    n = int(SR * .3); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t * 8) + 50) / SR) * np.exp(-t * 12) * 1.2 + rng.standard_normal(n) * np.exp(-t * 80) * .3
def ding(f=1568, d=.6):
    n = int(SR * d); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t * 6) * .5
def key():
    n = int(SR * .05); t = np.arange(n) / SR
    return rng.standard_normal(n) * np.exp(-t * 160) * .35
def tick():
    n = int(SR * .03); t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 200) * .5
def boom():
    n = int(SR * .9); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 3) + 38) / SR) * np.exp(-t * 4.5) * 1.4 + rng.standard_normal(n) * np.exp(-t * 30) * .5
add(4.8, swish(), .8); add(5.0, boom(), 1.0)
for s in [12.8, 18.68, 23.02, 28.49, 33.41, 36.75, 38.47]: add(s - 0.12, swish(), .42)
for a in (9.14, 9.75, 10.67): add(a, pop(), .45)
for k in range(14): add(13.15 + k * 0.07, key(), .5)
add(15.0, pop(), .4)
for a in (16.0, 16.4, 16.8): add(a, tick(), .5)
add(17.32, pop(), .45)
add(19.18, thump(), .6)
for k in range(5): add(20.92 + k * 0.28, tick(), .35)
for a in (25.2, 25.6, 26.0): add(a, pop(), .45)
add(26.84, boing(), .5)
add(30.7, key(), 1.0); add(31.9, key(), 1.0); add(31.52, swish(), .4)
for a in (33.91, 34.16, 34.41): add(a, pop(), .45)
add(35.29, thump(), .9)
add(37.0, boing(), .55)
add(38.97, pop(), .55); add(40.02, key(), .9); add(40.22, key(), .8); add(41.77, swish(), .5); add(42.1, ding(), .7)
y = y / np.max(np.abs(y)) * .85
w = wave.open('sfx.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype(np.int16).tobytes()); w.close(); print('ok')
