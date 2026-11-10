#!/usr/bin/env python3
"""Build a 9:16 reel (MP4) with kinetic typography: every frame is rendered by Chromium at an exact time.

Usage: python scripts/make_reel.py <reel spec json> <out.mp4>

Design (v3, 2026-11-08): text never zooms. Only the background photo moves (centered slow push-in).
Words pop in one by one, the keyword gets a violet box that wipes in, numbers count up, supporting lines sit
in white caption pills right under the headline (one tight block, centred in the Instagram safe area), a
segmented progress bar runs at the top, and scenes change with a quick zoom-blur cut.

Spec: {"id": ..., "music": {...}, "scenes": [scene, ...]}
Scene types ("t"):
  hook  first scene. Full-bleed real photo ("photo": repo path, or a dict resolved by remote_render in Actions),
        "chip", "title", "kw", optional "big" (number) and "sub" (one or two short lines).
  stat  "chip", "big" (counts up), "title", "kw", "sub". Optional "photo" (shown dimmed).
  list  "chip", "title", "kw", "rows": [["SK하이닉스", "-10.44%"], ...] (2-4 rows).
  text  "chip", "title", "kw", "lines": ["...", "..."] (2-3 short lines, shown as caption pills).
  cta   "title", "kw", "sub", "note" (small print: 정보 제공 목적 · 출처 ...).
  clip  (클립 트랙, 2026-11-10) another creator's / official video shown INSIDE the 정글저글 frame:
        {"t":"clip","clip":"clips/<file>.mp4","start":2.0,"sec":14,"title":"...","kw":"...",
         "credit":"@원작자 · TikTok","grade":"B"|"C","fit":"contain"(default, whole frame)|"cover"(crop to fill),
         "layout":"ekke"(default)|"box", "subs":[[0.0,2.4,"한글 자막"],...] (optional, times from the clip scene start),
         "more":"▼ 자세한 건 캡션에 ▼"}.
        layout "ekke" (2026-11-10 user decision: copy how ekke.now grew) = a whole reel that is just the clip:
        black frame, 정글저글 logo, bold 2-line title, credit, the video full-width in the middle (EKKE_BOX),
        optional Korean subtitles under it, and a '▼ 자세한 건 캡션에 ▼' line that sends viewers to the caption,
        where the money explanation lives. Clip length is the clip's own length (max CLIP_MAX_SEC); no share
        limit. layout "box" = the older short clip window (CLIP_BOX) followed by stat/text scenes.
        The text is drawn by Chromium, the video is composited by ffmpeg. Its ORIGINAL SOUND plays
        during the scene for every grade (user decision 2026-11-10) while the library track is ducked to CLIP_DUCK;
        optional "clip_volume" (default 1.0), "audio":"mute" only if the user asks for a specific clip.
        "credit" and "grade" are required. A clip scene may be the first scene (it is the moving hook); the
        title is fully visible from frame 0.
Every scene takes "sec" (default 3.5). Old v2 scenes ({"top","big","sub"}) are converted automatically.
Numbers: a leading "-" is shown in blue and "+" in red (Korean market convention: red = up, blue = down).
Audio ("music"): {"auto": mood} (default, rotating external free track, credit -> <out dir>/music_credit.txt),
{"mood": mood} (generated), {"file": path}, {"none": true}.
Requires Playwright/Chromium, Noto Sans CJK KR and ffmpeg.
"""
import base64
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
INK, VIOLET, BLUE, RED = "#0E0E12", "#6C3BFF", "#3D7BFF", "#FF3B30"
OUT_T = 0.22  # length of the exit cut
CLIP_BOX = (72, 640, 936, 820)  # x, y, w, h of the video window in a clip scene (above the 430 px bottom safe area)
EKKE_BOX = (0, 610, 1080, 720)  # full-width video in the ekke layout (16:9 fills it; vertical clips are pillarboxed)
CLIP_MAX_SEC = 60.0  # 2026-11-10: ekke.now used the whole viral clip, so no 5 s / 40 % limit any more
CLIP_DUCK = 0.18  # library track volume while a clip's original sound plays


def esc(s):
    return html.escape(str(s))


def convert_v2(sc, i, n):
    if "t" in sc:
        return sc
    out = {"sec": sc.get("sec", 3.5), "title": sc.get("top", "").replace("\n", " "), "kw": sc.get("kw")}
    sub = [x for x in sc.get("sub", "").split("\n") if x]
    if i == n - 1:
        return {**out, "t": "cta", "sub": sub[0] if sub else "", "note": " · ".join(sub[1:])}
    if sc.get("big"):
        return {**out, "t": "hook" if i == 0 else "stat", "big": sc["big"], "sub": sub}
    return {**out, "t": "text", "lines": sub}


def photo_data_uri(photo):
    if not isinstance(photo, str) or not photo:
        return None
    if photo.startswith(("http", "data:")):
        return photo
    path = (ROOT / photo) if not Path(photo).is_absolute() else Path(photo)
    if not path.exists():
        return None
    mime = {".png": "image/png", ".webp": "image/webp"}.get(path.suffix.lower(), "image/jpeg")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def words_html(text, kw, start, step=0.07):
    """Split a headline into words that pop in; the keyword gets the violet wipe box."""
    parts, t = [], start

    def plain(chunk):
        nonlocal t
        for tok in re.split(r"(\s+)", chunk):
            if not tok:
                continue
            if "\n" in tok:
                parts.append("<br>")
            elif tok.isspace():
                parts.append(" ")
            else:
                parts.append(f'<span class="w" data-a="pop" data-s="{t:.2f}">{esc(tok)}</span>')
                t += step

    if kw and kw in text:
        before, after = text.split(kw, 1)
        plain(before)
        parts.append(f'<span class="kw" data-a="wipe" data-s="{t:.2f}"><i></i><b data-a="pop" data-s="{t + .05:.2f}">{esc(kw)}</b></span>')
        t += step * 2
        plain(after)
    else:
        plain(text)
    return "".join(parts), t


def big_html(big, start):
    color = BLUE if big.strip().startswith(("-", "−", "▼")) else RED if big.strip().startswith(("+", "▲")) else "#fff"
    return f'<div class="big" data-a="count" data-s="{start:.2f}" data-v="{esc(big)}" style="color:{color}">{esc(big)}</div>'


def pills(lines, start, step=0.12):
    out = []
    for k, line in enumerate(lines):
        out.append(f'<div class="pill" data-a="rise" data-s="{start + k * step:.2f}">{esc(line)}</div>')
    return "".join(out), start + len(lines) * step


def scene_html(sc, idx, n, sec):
    t = sc["t"]
    chip = f'<div class="chip" data-a="rise" data-s="0.05">{esc(sc["chip"])}</div>' if sc.get("chip") else ""
    title, nt = words_html(sc.get("title", ""), sc.get("kw"), 0.15)
    big = ""
    if sc.get("big"):
        big = big_html(sc["big"], 0.1 if t == "stat" else nt)
        nt = max(nt, 0.6)
    sub = sc.get("sub") or []
    sub = [sub] if isinstance(sub, str) else sub
    body = ""
    if t == "list":
        rows = "".join(
            f'<div class="row" data-a="slide" data-s="{nt + k * .14:.2f}"><span>{esc(a)}</span>'
            f'<span class="rv" style="color:{BLUE if str(b).startswith("-") else RED if str(b).startswith("+") else "#fff"}">{esc(b)}</span></div>'
            for k, (a, b) in enumerate(sc.get("rows", [])))
        body = f'<div class="rows">{rows}</div>'
    elif t == "text":
        body, _ = pills(sc.get("lines", []), nt + .05)
    elif sub:
        body, _ = pills(sub, nt + .1)
    order = (big + f'<div class="title">{title}</div>') if t == "stat" else (f'<div class="title">{title}</div>' + big)
    if t == "cta":
        body = (f'<div class="save" data-a="pop" data-s="{nt + .1:.2f}">💾 저장 &nbsp;·&nbsp; 💬 댓글로 알려주셈</div>' +
                (pills(sub, nt + .3)[0] if sub else ""))
        note = f'<div class="note" data-a="rise" data-s="{nt + .5:.2f}">{esc(sc.get("note", ""))}</div>' if sc.get("note") else ""
    else:
        note = ""
    photo = photo_data_uri(sc.get("photo"))
    if photo:
        dim = ".35" if t == "hook" else ".62"
        bg = (f'<div class="bg" data-a="push" style="background:url(\'{photo}\') center/cover"></div>'
              f'<div class="shade" style="background:linear-gradient(180deg,rgba(0,0,0,{dim}) 0%,rgba(0,0,0,{dim}) 30%,rgba(0,0,0,.78) 100%)"></div>')
    else:
        bg = ('<div class="bg blob" data-a="drift"></div>'
              '<div class="shade" style="background:radial-gradient(circle at 50% 120%,rgba(108,59,255,.28),rgba(0,0,0,0) 60%)"></div>')
    if photo and sc.get("credit") and sc.get("credit_on_image"):  # credits go in the caption (user request 2026-11-09)
        note += f'<div class="credit">📷 {esc(sc["credit"])}</div>'
    main = f'<div class="block">{chip}{order}{body}</div>'
    if t == "clip" and sc.get("layout", "ekke") == "ekke":
        x, y, w, h = clip_box(sc)
        subs = json.dumps(sc.get("subs") or [], ensure_ascii=False)
        bg, note = "", ""
        main = (f'<div class="etop"><div class="title etitle">{title}</div>'
                f'<div class="ccredit">🎥 {esc(sc.get("credit", ""))}</div></div>'
                f'<div class="clipbox" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>'
                f'<div class="esub" data-a="subs" data-v="{esc(subs)}"></div>'
                f'<div class="emore">{esc(sc.get("more", "▼ 자세한 건 캡션에 ▼"))}</div>')
    elif t == "clip":
        x, y, w, h = CLIP_BOX
        main = (f'<div class="ctop">{chip}<div class="title ctitle">{title}</div>'
                f'<div class="ccredit">🎥 {esc(sc.get("credit", ""))}</div></div>'
                f'<div class="clipbox" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>')
    segs = "".join(f'<div class="seg"><div class="fill" data-seg="{k}"></div></div>' for k in range(n))
    return f"""<html><head><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;background:{INK};color:#fff;font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif;word-break:keep-all;overflow:hidden}}
#stage{{position:absolute;inset:0;transform-origin:50% 50%}}
.bg{{position:absolute;inset:-2%;transform-origin:50% 50%}}
.blob{{background:radial-gradient(circle at 25% 30%,rgba(108,59,255,.55) 0,rgba(108,59,255,0) 38%),
  radial-gradient(circle at 80% 70%,rgba(61,123,255,.35) 0,rgba(61,123,255,0) 40%),{INK}}}
.shade{{position:absolute;inset:0}}
.top{{position:absolute;top:196px;left:72px;right:72px;display:flex;flex-direction:column;gap:18px}}
.brand{{font-size:30px;font-weight:900;letter-spacing:-.5px;opacity:.95}}
.bar{{display:flex;gap:8px}}.seg{{flex:1;height:7px;border-radius:4px;background:rgba(255,255,255,.28);overflow:hidden}}
.fill{{height:100%;width:0;background:#fff}}
.block{{position:absolute;left:72px;right:72px;top:300px;bottom:470px;display:flex;flex-direction:column;
  justify-content:center;align-items:center;text-align:center;gap:30px}}
.chip{{white-space:nowrap;display:inline-block;background:{VIOLET};color:#fff;font-weight:900;font-size:38px;padding:10px 26px;border-radius:999px}}
.title{{font-size:{104 if t == "hook" else 92}px;font-weight:900;line-height:1.22;letter-spacing:-3px;text-shadow:0 4px 24px rgba(0,0,0,.35)}}
.w,.kw{{display:inline-block}}
.kw{{position:relative;padding:0 14px;margin:0 2px}}
.kw i{{position:absolute;inset:6px 0 2px 0;background:{VIOLET};border-radius:14px;transform-origin:0 50%}}
.kw b{{position:relative;display:inline-block;font-weight:900}}
.big{{font-size:{210 if len(sc.get("big", "")) <= 7 else 160}px;font-weight:900;letter-spacing:-6px;line-height:1;font-variant-numeric:tabular-nums;text-shadow:0 6px 40px rgba(0,0,0,.4)}}
.pill{{white-space:nowrap;background:#fff;color:{INK};font-size:46px;font-weight:800;line-height:1.35;padding:14px 30px;border-radius:20px;max-width:100%}}
.rows{{width:100%;display:flex;flex-direction:column;gap:18px}}
.row{{display:flex;justify-content:space-between;align-items:center;background:rgba(255,255,255,.1);border:2px solid rgba(255,255,255,.14);
  border-radius:28px;padding:28px 40px;font-size:52px;font-weight:800}}
.rv{{font-size:72px;font-weight:900;letter-spacing:-2px}}
.save{{font-size:50px;font-weight:900;background:{VIOLET};padding:18px 36px;border-radius:999px}}
.credit{{position:absolute;right:72px;bottom:430px;font-size:24px;color:rgba(255,255,255,.7)}}
.ctop{{position:absolute;left:72px;right:72px;top:262px;height:360px;display:flex;flex-direction:column;
  justify-content:flex-end;align-items:center;text-align:center;gap:14px}}
.ctitle{{font-size:76px;letter-spacing:-2px;line-height:1.18}}
.ccredit{{font-size:30px;font-weight:700;color:rgba(255,255,255,.82)}}
.clipbox{{position:absolute;background:#000;box-shadow:0 0 0 4px rgba(255,255,255,.18)}}
.etop{{position:absolute;left:60px;right:60px;top:250px;height:340px;display:flex;flex-direction:column;
  justify-content:flex-end;align-items:center;text-align:center;gap:16px}}
.etitle{{font-size:{78 if len(sc.get("title", "")) <= 22 else 66}px;letter-spacing:-2px;line-height:1.2}}
.esub{{position:absolute;left:60px;right:60px;top:{EKKE_BOX[1] + EKKE_BOX[3] + 22}px;text-align:center;font-size:44px;font-weight:800;
  line-height:1.3;color:#FFE14D;text-shadow:0 2px 0 #000,0 0 12px rgba(0,0,0,.8)}}
.emore{{position:absolute;left:60px;right:60px;top:1418px;text-align:center;font-size:36px;font-weight:900;color:{VIOLET};
  filter:brightness(1.5)}}
.note{{position:absolute;left:72px;right:72px;bottom:430px;text-align:center;font-size:28px;line-height:1.5;color:rgba(255,255,255,.72)}}
</style></head><body><div id="stage">{bg}
<div class="top"><div class="brand">정글저글</div><div class="bar">{segs}</div></div>
{main}{note}</div>
<script>
(()=>{{
const IDX={idx}, SEC={sec}, OUT={OUT_T};
const cl=(x)=>Math.max(0,Math.min(1,x)), eo=(x)=>1-Math.pow(1-x,3), back=(x)=>{{const c=1.9;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)}};
const els=[...document.querySelectorAll('[data-a]')];
// keep caption pills and chips on one line: shrink the font until they fit the safe width (never wrap mid-phrase)
for(const e of document.querySelectorAll('.pill,.chip')){{let fs=parseFloat(getComputedStyle(e).fontSize);
  while(e.scrollWidth>{W - 144} && fs>26){{fs-=1;e.style.fontSize=fs+'px'}}}}
function fmt(src,p){{
  const m=src.match(/^([^0-9]*)([0-9][0-9,]*(?:\\.[0-9]+)?)(.*)$/);
  if(!m||/[0-9]/.test(m[3])) return src;
  const raw=m[2].replace(/,/g,''), dec=(raw.split('.')[1]||'').length, v=parseFloat(raw)*p;
  let s=v.toFixed(dec); if(m[2].includes(',')){{const [a,b]=s.split('.');s=a.replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,',')+(b?'.'+b:'')}}
  return m[1]+s+m[3];
}}
window.seek=(t0)=>{{
  // Hook scene: the headline is already fully on screen at frame 0 (no pop-in), so the paused first frame,
  // the feed preview and the default cover never look empty. Later scenes keep their entrance animations.
  const t = IDX===0 ? t0+2.5 : t0;
  for(const e of els){{
    const a=e.dataset.a, s=parseFloat(e.dataset.s||0);
    if(a==='pop'){{const p=cl((t-s)/.32);e.style.opacity=cl(p*2.5);e.style.transform=`translateY(${{(1-eo(p))*40}}px) scale(${{.7+.3*back(p)}})`}}
    else if(a==='rise'){{const p=eo(cl((t-s)/.4));e.style.opacity=p;e.style.transform=`translateY(${{(1-p)*36}}px)`}}
    else if(a==='slide'){{const p=eo(cl((t-s)/.42));e.style.opacity=p;e.style.transform=`translateX(${{(1-p)*120}}px)`}}
    else if(a==='wipe'){{const p=eo(cl((t-s-.12)/.35));e.querySelector('i').style.transform=`scaleX(${{p}})`}}
    else if(a==='count'){{const p=cl((t-s)/.9);e.style.opacity=cl(p*4);e.style.transform=`scale(${{.85+.15*back(cl(p*1.4))}})`;e.textContent=fmt(e.dataset.v,eo(p))}}
    else if(a==='push'){{e.style.transform=`scale(${{1.12-.1*cl(t0/SEC)}})`}}
    else if(a==='subs'){{const cur=JSON.parse(e.dataset.v).find(x=>t0>=x[0]&&t0<x[1]);e.textContent=cur?cur[2]:''}}
    else if(a==='drift'){{e.style.transform=`translate(${{Math.sin(t0*.6)*30}}px,${{Math.cos(t0*.5)*24}}px)`}}
  }}
  document.querySelectorAll('[data-seg]').forEach(f=>{{const k=+f.dataset.seg;f.style.width=(k<IDX?100:k>IDX?0:cl(t0/SEC)*100)+'%'}});
  const st=document.getElementById('stage');
  const pin=IDX===0?1:eo(cl(t0/.2)), pout=cl((t0-(SEC-OUT))/OUT);
  st.style.opacity=Math.min(.35+.65*pin,1-pout);
  st.style.transform=`scale(${{(0.97+0.03*pin)*(1+.07*pout)}})`;
  st.style.filter=pout>0?`blur(${{pout*10}}px)`:(pin<1?`blur(${{(1-pin)*6}}px)`:'none');
}};
}})();
</script></body></html>"""


def pick_audio(spec, out, total, tmp):
    music = spec.get("music", {"auto": "upbeat"})
    credit_file = out.parent / "music_credit.txt"
    credit_file.unlink(missing_ok=True)
    sys.path.insert(0, str(ROOT / "scripts"))
    if music.get("auto"):
        import music_library  # rotate through the external free-music library, no repeats
        picked = music_library.pick(music["auto"], spec.get("id", out.stem))
        if picked:
            credit_file.write_text(picked["credit"] + "\n", encoding="utf-8")
            print(f"music: {picked['credit']}")
            return ["-stream_loop", "-1", "-i", str(ROOT / picked["file"])]
        music = {"mood": music["auto"]}
    if music.get("none"):
        return ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    if music.get("file"):
        # a pinned library track still needs its CC credit in the caption and a usage record for rotation
        import music_library
        lib = {t["file"]: t for t in music_library.load(music_library.LIB_JSON, [])}
        t = lib.get(music["file"])
        if t:
            credit_file.write_text(f"🎵 {t['title']} - {t['artist']} ({t['license']})\n", encoding="utf-8")
            usage = music_library.load(music_library.USAGE_JSON, [])
            usage.append({"reel": spec.get("id", out.stem), "mood": t["mood"], "file": t["file"],
                          "at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds")})
            music_library.save(music_library.USAGE_JSON, usage[-500:])
            print(f"music (pinned): {t['title']} - {t['artist']}")
        return ["-stream_loop", "-1", "-i", str(ROOT / music["file"])]
    import music as music_gen  # scripts/music.py
    track = str(Path(tmp) / "music.wav")
    music_gen.write_wav(track, music_gen.generate(music.get("mood", "upbeat"), total + 0.5, spec.get("id", out.stem)))
    return ["-i", track]


def clip_box(sc):
    return EKKE_BOX if sc.get("layout", "ekke") == "ekke" else CLIP_BOX


def check_clips(scenes, total):
    """클립 트랙 rules (CLAUDE.md '클립 트랙'). Returns [(scene index, start time in reel, scene)]."""
    clips, t = [], 0.0
    for i, sc in enumerate(scenes):
        sec = float(sc.get("sec", 3.5))
        if sc.get("t") == "clip":
            path = ROOT / sc.get("clip", "")
            if not sc.get("clip") or not path.is_file():
                raise ValueError(f"scene {i + 1}: clip file not found ({sc.get('clip')})")
            if sc.get("grade") not in ("B", "C"):  # user decision 2026-11-10: no grade A (permission DMs)
                raise ValueError(f"scene {i + 1}: clip needs \"grade\": \"B\"|\"C\" (A등급은 쓰지 않음)")
            if not str(sc.get("credit", "")).strip():
                raise ValueError(f"scene {i + 1}: clip needs \"credit\" (원작자 표기)")
            if sec > CLIP_MAX_SEC + 1e-6:
                raise ValueError(f"scene {i + 1}: clip scene {sec}s > {CLIP_MAX_SEC}s")
            clips.append((i, t, sc))
        t += sec
    return clips


def overlay_clips(silent, clips, tmp):
    """Composite each clip into CLIP_BOX during its scene; the clip's own audio is never mapped."""
    if not clips:
        return silent
    args, chains, last = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent)], [], "[0:v]"
    for k, (_, t0, sc) in enumerate(clips, 1):
        x, y, w, h = clip_box(sc)
        sec = float(sc.get("sec", 3.5))
        show = max(0.1, sec - OUT_T)
        args += ["-ss", f"{float(sc.get('start', 0)):.2f}", "-t", f"{show:.2f}", "-i", str(ROOT / sc["clip"])]
        fit = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}" if sc.get("fit") == "cover" else
               f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black")
        chains.append(f"[{k}:v]fps={FPS},{fit},setsar=1,setpts=PTS-STARTPTS+{t0:.3f}/TB[c{k}]")
        nxt = f"[v{k}]"
        chains.append(f"{last}[c{k}]overlay={x}:{y}:enable='between(t,{t0:.3f},{t0 + show:.3f})':eof_action=pass{nxt}")
        last = nxt
    out = Path(tmp) / "video_clips.mp4"
    subprocess.run([*args, "-filter_complex", ";".join(chains), "-map", last, "-an", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "18", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def has_audio(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0",
                        str(path)], capture_output=True, text=True)
    return bool(r.stdout.strip())


def mix_clip_audio(clips, master):
    """Original clip sound plays during its scene (user decision 2026-11-10, every grade); the library track is
    ducked to CLIP_DUCK while a clip plays. Inputs: 0 = video, 1 = music, 2.. = clip audio."""
    ins, parts, duck, labels = [], [], [], ["[m]"]
    k = 2
    for _, t0, sc in clips:
        show = max(0.1, float(sc.get("sec", 3.5)) - OUT_T)
        duck.append(f"volume={CLIP_DUCK}:enable='between(t,{t0:.3f},{t0 + show:.3f})'")
        if sc.get("audio", "keep") == "mute" or not has_audio(ROOT / sc["clip"]):
            continue
        ins += ["-ss", f"{float(sc.get('start', 0)):.2f}", "-t", f"{show:.2f}", "-i", str(ROOT / sc["clip"])]
        ms = int(round(t0 * 1000))
        parts.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.08,afade=t=out:st={max(0.0, show - 0.15):.2f}:d=0.15,"
                     f"volume={float(sc.get('clip_volume', 1.0)):.2f},adelay={ms}|{ms}[c{k}]")
        labels.append(f"[c{k}]")
        k += 1
    if not clips:
        return [], ""
    music = "[1:a]aformat=sample_rates=48000:channel_layouts=stereo," + ",".join(duck) + "[m]"
    mix = (f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0," if len(labels) > 1 else f"{labels[0]}") + master
    return ins, ";".join([music, *parts, mix + "[aout]"])


def main(spec_path, out_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    raw = spec["scenes"]
    scenes = [convert_v2(sc, i, len(raw)) for i, sc in enumerate(raw)]
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    total = sum(float(sc.get("sec", 3.5)) for sc in scenes)
    clips = check_clips(scenes, total)
    with tempfile.TemporaryDirectory() as tmp:
        silent = Path(tmp) / "video.mp4"
        enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg",
                                "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(silent)],
                               stdin=subprocess.PIPE)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": W, "height": H})
            for i, sc in enumerate(scenes):
                sec = float(sc.get("sec", 3.5))
                page.goto("about:blank")  # fresh document and script scope for every scene
                page.set_content(scene_html(sc, i, len(scenes), sec), wait_until="load")
                if page.evaluate("typeof window.seek") != "function":
                    raise RuntimeError(f"scene {i + 1}: animation script failed to load")
                page.evaluate("document.fonts.ready")
                for f in range(int(round(sec * FPS))):
                    page.evaluate(f"seek({f / FPS})")
                    enc.stdin.write(page.screenshot(type="jpeg", quality=92))
            browser.close()
        enc.stdin.close()
        if enc.wait() != 0:
            raise RuntimeError("ffmpeg video encode failed")
        silent = overlay_clips(silent, clips, tmp)
        audio_in = pick_audio(spec, out, total, tmp)
        master = f"loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:d=0.3,afade=t=out:st={max(0.0, total - 1.2)}:d=1.2"
        clip_in, graph = mix_clip_audio(clips, master)
        afilter = ["-filter_complex", graph, "-map", "[aout]"] if graph else ["-af", master, "-map", "1:a:0"]
        # video must be stream 0: an audio-first MP4 (2026-11-10) passed container processing but every
        # media_publish then failed with "Fatal [OAuthException (-1)]"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), *audio_in, *clip_in,
                        "-map", "0:v:0", *afilter, "-t", f"{total:.2f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-ar", "48000", "-movflags", "+faststart", str(out)], check=True)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
