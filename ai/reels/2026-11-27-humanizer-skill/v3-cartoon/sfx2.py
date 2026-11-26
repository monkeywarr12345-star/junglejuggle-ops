import numpy as np, wave
SR = 48000; D = 37.9
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
SC = [3.37, 7.24, 8.83, 13.17, 16.11, 17.82, 19.46, 22.17, 25.85, 28.94, 31.67, 32.9]
for s in SC: add(s - 0.12, swish(), .45)
add(0.02, pop(), .6); add(1.34, boing(), .5)
for a in (1.55, 1.85, 2.15): add(a, pop(), .35)
add(2.32, thump(), .8)
for k in range(13): add(3.93 + k * 0.08, tick(), .5)
for i in range(5): add(4.05 + i * .27, pop(), .35)
add(5.5, swish(), .6)
add(7.84, boing(), .5); add(8.1, pop(), .4); add(10.17, pop(), .4); add(11.4, pop(), .4)
add(13.3, boing(), .4); add(15.33, ding(1760, .5), .6)
for a in (16.3, 16.6, 16.9): add(a, pop(), .45)
add(18.97, pop(), .6); add(19.05, boing(), .4)
add(21.15, ding(), .5)
for k in range(10): add(23.33 + k * 0.1, key(), .7)
add(24.45, pop(), .5); add(24.8, thump(), .7)
add(27.02, swish(), .5); add(30.5, thump(), .7); add(31.05, swish(), .7)
add(31.77, boing(), .6)
add(33.15, key(), .9); add(33.4, key(), .8); add(34.75, ding(), .7)
y = y / np.max(np.abs(y)) * .85
w = wave.open('sfx.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype(np.int16).tobytes()); w.close(); print('ok')
