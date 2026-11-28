import numpy as np, wave
SR = 48000; D = 38.0
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
SC = [4.03, 6.75, 11.86, 15.17, 18.24, 19.63, 22.27, 24.35, 27.28, 30.37, 32.69]
for s in SC: add(s - 0.12, swish(), .45)
add(0.02, pop(), .6); add(0.1, boing(), .4)
for i in range(5): add(1.45 + i * .18, pop(), .35)
add(2.92, thump(), .85)
add(4.8, pop(), .5)
for a in (6.78, 7.91, 8.62, 9.24, 10.19): add(a, pop(), .45)
for i in range(3): add(11.95 + i * .25, tick(), .5)
add(13.44, boing(), .45)
for i in range(3): add(13.7 + i * .4, pop(), .3)
add(15.25, swish(), .5); add(15.45, ding(1760, .5), .5)
for a in (16.75, 17.0, 17.25): add(a, pop(), .45)
add(18.24 + 0.7, pop(), .6)
for k in range(12): add(18.24 + 0.8 + k * 0.045, key(), .5)
for k in range(16): add(19.63 + 0.3 + k * 0.1, key(), .6)
add(19.63 + 2.0, pop(), .5)
add(22.27 + 0.6, thump(), .4); add(22.27 + 1.05, thump(), .4); add(22.27 + 1.5, thump(), .85)
for k in range(5): add(24.35 + 0.75 + k * 0.1, key(), .8)
add(24.35 + 1.35, pop(), .6); add(24.35 + 1.5, ding(), .45)
add(27.28 + 0.5, swish(), .4); add(27.28 + 1.0, swish(), .4)
add(30.47, boing(), .6)
add(33.4, key(), .9); add(33.6, key(), .8); add(35.4, swish(), .5); add(35.75, ding(), .7)
y = y / np.max(np.abs(y)) * .85
w = wave.open('sfx.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype(np.int16).tobytes()); w.close(); print('ok')
