import numpy as np, wave
SR = 48000; D = 37.0
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
for a in (0.5, 1.15, 1.8, 2.45): add(a, thump(), .22)
add(3.35, swish(), .35); add(4.25, ding(2637, .7), .45)
add(4.97, thump(), 1.0); add(4.95, swish(), .6)
SC = [7.43, 8.94, 13.65, 16.02, 17.66, 19.62, 21.99, 24.36, 27.05, 28.94, 31.34]
for s in SC: add(s - 0.12, swish(), .42)
add(5.87, pop(), .45)
for a in (9.24, 9.94, 10.89): add(a, pop(), .4)
add(14.65, pop(), .4)
for a in (16.27, 16.57, 16.87): add(a, pop(), .45)
add(17.66 + 0.72, pop(), .55); add(17.66 + 1.42, pop(), .55)
for k in range(18): add(19.92 + k * 0.08, key(), .55)
add(21.99 + 0.6, pop(), .5); add(21.99 + 1.3, pop(), .45); add(21.99 + 1.5, thump(), .8)
add(24.76, swish(), .45); add(24.95, ding(), .45)
for j in range(5): add(27.35 + j * 0.12, tick(), .4)
add(29.29, boing(), .55)
add(31.84, pop(), .55); add(32.79, key(), .9); add(32.96, key(), .8); add(34.44, swish(), .5); add(34.8, ding(), .7)
y = y / np.max(np.abs(y)) * .85
w = wave.open('sfx.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype(np.int16).tobytes()); w.close(); print('ok')
