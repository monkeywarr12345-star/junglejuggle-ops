"""usage: caps2.py voice.wav clip1_dur out_tl.json
Phrase captions aligned to Ludyte speech: syllable-proportional over voiced time, snapped to pauses."""
import sys, re, json, subprocess
wav, c1, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
# (line id, phrase html)
PH = [
 ("s1", "노션, 챗GPT, 캡컷"), ("s1", "이거 돈 내고 쓰면<br/><b>손해</b>예요"),
 ("s2", "똑같이 쓰는 <b>무료 버전</b>이<br/>있거든요"),
 ("s3", "노션 대신 AppFlowy"), ("s3", "<b>표까지 공짜</b>예요"),
 ("s4", "ChatGPT 대신 Ollama"), ("s4", "<b>내 컴퓨터</b>에서<br/>AI를 무료로 돌려요"),
 ("s5", "캡컷 대신 Kdenlive"), ("s5", "<b>자동 자막</b>까지 다 돼요"),
 ("s6", "전부 코드가 공개된<br/>오픈소스라"), ("s6", "구독료가 <b>0원</b>이에요"),
 ("s7", "뭘 바꿀지는<br/><b>클로드</b>한테 물어보면 돼요"),
 ("s8", "댓글에 <b>'무료'</b> 남기면"), ("s8", "프롬프트<br/>보내드릴게요"),
]
SPOKEN = {"노션, 챗GPT, 캡컷": "노션챗지피티캡컷", "노션 대신 AppFlowy": "노션대신앱플로위", "ChatGPT 대신 Ollama": "챗지피티대신올라마",
          "캡컷 대신 Kdenlive": "캡컷대신케이덴라이브", "구독료가 <b>0원</b>이에요": "구독료가영원이에요"}
def syl(h):
    if h in SPOKEN: return len(SPOKEN[h])
    t = re.sub(r"<[^>]+>", "", h); return max(1, len(re.findall(r"[가-힣A-Za-z0-9]", t)))
err = subprocess.run(["ffmpeg", "-nostdin", "-i", wav, "-af", "silencedetect=n=-36dB:d=0.12", "-f", "null", "-"], capture_output=True, text=True).stderr
ss = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", err)]; se = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", err)]
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav], capture_output=True, text=True).stdout)
sil = list(zip(ss, se + [dur] * (len(ss) - len(se))))
def voiced(a, b):
    segs = []; t = a
    for s, e in sorted(sil):
        if e <= a or s >= b: continue
        if s > t: segs.append((t, min(s, b)))
        t = max(t, e)
    if t < b: segs.append((t, b))
    return segs
caps = []
for part, (a, b) in enumerate([(0, c1), (c1, dur)]):
    ph = [p for p in PH if (p[0] in ("s1", "s2", "s3", "s4")) == (part == 0)]
    v = voiced(a, b); tot = sum(e - s for s, e in v)
    st, en = v[0][0], v[-1][1]
    def at(frac):
        x = frac * tot
        for s, e in v:
            if x <= e - s: return s + x
            x -= e - s
        return en
    W = sum(syl(p[1]) for p in ph); acc = 0; bounds = [st]
    mids = [(s + e) / 2 for s, e in sil if s > st + .1 and e < en - .1]
    for p in ph[:-1]:
        acc += syl(p[1]); x = at(acc / W)
        near = [m for m in mids if abs(m - x) < .45]
        bounds.append(min(near, key=lambda m: abs(m - x)) if near else x)
    bounds.append(en)
    for i, p in enumerate(ph):
        caps.append([round(bounds[i], 3), round(bounds[i + 1], 3), p[1], p[0]])
for i in range(len(caps) - 1):
    caps[i][1] = caps[i + 1][0]
caps[-1][1] = dur
s = {}
for c in caps:
    s.setdefault(c[3], [c[0], c[1]]); s[c[3]][1] = c[1]
ids = sorted(s, key=lambda k: int(k[1:]))
s[ids[0]][0] = 0.0
for i in range(len(ids) - 1): s[ids[i]][1] = s[ids[i + 1]][0]
s[ids[-1]][1] = dur
t = {"dur": round(dur, 3), "s": s, "caps": caps, "kw": "무료", "sil": sil}
json.dump(t, open(out, "w"), ensure_ascii=False)
for c in caps: print(c)
print(s)
