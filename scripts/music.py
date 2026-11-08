#!/usr/bin/env python3
"""Generate original background music for reels (no third-party audio, so no copyright claims).

Usage: python scripts/music.py <mood> <seconds> <out.wav> [seed]
  mood: upbeat | tense | chill
  seed: any string; the same seed gives the same track, different seeds vary key, progression and patterns.

numpy/scipy synthesis: kick, snare, hats, bass, chord pad and a pluck arpeggio.
"""
import hashlib
import sys
import wave

import numpy as np
from scipy.signal import butter, lfilter

SR = 44100

MOODS = {
    "upbeat": {"bpm": 112, "scale": "major", "progs": [[0, 7, 9, 5], [0, 5, 9, 7], [9, 5, 0, 7]], "swing": 0.0, "hat": 1.0},
    "tense": {"bpm": 96, "scale": "minor", "progs": [[0, 8, 3, 10], [0, 5, 8, 7], [0, 10, 8, 7]], "swing": 0.0, "hat": 0.8},
    "chill": {"bpm": 84, "scale": "major", "progs": [[0, 9, 5, 7], [5, 4, 2, 0], [0, 4, 9, 5]], "swing": 0.12, "hat": 0.6},
}
MAJOR, MINOR = [0, 2, 4, 5, 7, 9, 11], [0, 2, 3, 5, 7, 8, 10]


def rng_from(seed):
    return np.random.default_rng(int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16))


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def env(n, attack=0.005, decay=0.2):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / max(decay, 1e-4))


def lowpass(x, cutoff, order=2):
    b, a = butter(order, cutoff / (SR / 2), btype="low")
    return lfilter(b, a, x)


def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f * (1 + detune)) % 1.0) - 1


def tri(f, n):
    return 2 * np.abs(saw(f, n)) - 1


def chord_tones(root_degree_semitones, key, scale):
    # Build a triad (plus 7th) from the scale, starting at the given semitone offset from the key.
    steps = MAJOR if scale == "major" else MINOR
    root = key + root_degree_semitones
    pcs = [(root - key) % 12]
    idx = min(range(7), key=lambda i: abs(steps[i] - pcs[0]))
    notes = [root]
    for k in (2, 4, 6):
        s = steps[(idx + k) % 7] + 12 * ((idx + k) // 7) - steps[idx]
        notes.append(root + s)
    return notes


def generate(mood, seconds, seed="jj"):
    cfg = MOODS[mood]
    rng = rng_from(f"{mood}-{seed}")
    bpm = cfg["bpm"] + int(rng.integers(-4, 5))
    beat = 60.0 / bpm
    key = 48 + int(rng.integers(0, 7))  # C3..F#3
    prog = cfg["progs"][int(rng.integers(0, len(cfg["progs"])))]
    n = int(seconds * SR)
    mix_l, mix_r = np.zeros(n), np.zeros(n)

    def add(sig, start, pan=0.0, gain=1.0):
        s = int(start * SR)
        if s >= n:
            return
        e = min(n, s + len(sig))
        seg = sig[: e - s] * gain
        mix_l[s:e] += seg * (1 - max(pan, 0))
        mix_r[s:e] += seg * (1 + min(pan, 0))

    # Instruments
    kn = int(0.35 * SR)
    kt = np.arange(kn) / SR
    kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-kt * 30)) * kt) * env(kn, 0.001, 0.18)
    sn = int(0.25 * SR)
    snare = (rng.standard_normal(sn) * 0.6 + np.sin(2 * np.pi * 190 * np.arange(sn) / SR) * 0.4) * env(sn, 0.001, 0.09)
    hn = int(0.06 * SR)
    hat = np.diff(rng.standard_normal(hn + 1)) * env(hn, 0.0005, 0.018)

    bar = beat * 4
    bars = int(np.ceil(seconds / bar)) + 1
    arp_pattern = rng.permutation([0, 1, 2, 3, 2, 1, 3, 0])
    drums_from = 1 if rng.random() < 0.7 else 0  # usually one bar of intro without drums
    for b in range(bars):
        t0 = b * bar
        notes = chord_tones(prog[b % len(prog)], key, cfg["scale"])
        # pad
        pn = int(bar * SR)
        pad = sum(0.5 * saw(hz(m + 12), pn, d) + 0.5 * saw(hz(m + 12), pn, -d) for m, d in zip(notes[:3], (0.003, 0.002, 0.004)))
        pad = pad * np.minimum(1, np.arange(pn) / (0.15 * SR)) * np.minimum(1, (pn - np.arange(pn)) / (0.1 * SR))
        add(lowpass(pad, 1600 if mood != "chill" else 1100) / 6, t0, gain=0.42)
        # bass on eighths (root, octave on the off-beat for upbeat)
        for k in range(8):
            bn = int(beat / 2 * SR)
            f = hz(notes[0] - 12 + (12 if (mood == "upbeat" and k % 2) else 0))
            add(lowpass(tri(f, bn), 500) * env(bn, 0.003, 0.18), t0 + k * beat / 2, gain=0.7)
        # pluck arpeggio on sixteenths for upbeat/tense, eighths for chill
        div = 4 if mood != "chill" else 2
        for k in range(4 * div):
            tone = notes[arp_pattern[k % 8] % 4] + 24
            an = int(beat / div * SR * 0.95)
            sw = cfg["swing"] * beat / div if (k % 2) else 0
            add(lowpass(saw(hz(tone), an), 2600) * env(an, 0.002, 0.12), t0 + k * beat / div + sw, pan=0.3 if k % 2 else -0.3, gain=0.12)
        if b >= drums_from:
            for k in range(4):
                if mood == "tense" or k in (0, 2) or (mood == "upbeat"):
                    add(kick, t0 + k * beat, gain=0.9 if k in (0, 2) else 0.6)
                if k in (1, 3):
                    add(snare, t0 + k * beat, gain=0.35)
            for k in range(8):
                sw = cfg["swing"] * beat / 2 if k % 2 else 0
                add(hat, t0 + k * beat / 2 + sw, pan=0.4, gain=0.25 * cfg["hat"] * (1.0 if k % 2 else 0.7))

    # master: gentle lowpass on chill, fades, normalize
    stereo = np.stack([mix_l, mix_r], axis=1)
    top = 5000 if mood == "chill" else 9000
    stereo = np.stack([lowpass(stereo[:, 0], top), lowpass(stereo[:, 1], top)], axis=1)
    fade = int(min(1.5, seconds / 6) * SR)
    stereo[:int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))[:, None]
    stereo[-fade:] *= np.linspace(1, 0, fade)[:, None]
    stereo = np.tanh(stereo * 1.2)
    stereo /= max(1e-6, np.abs(stereo).max()) / 0.89
    return stereo


def write_wav(path, stereo):
    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    mood, secs, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    seed = sys.argv[4] if len(sys.argv) > 4 else out
    write_wav(out, generate(mood, secs, seed))
    print(out)
