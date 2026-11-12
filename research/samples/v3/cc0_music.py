"""Pick a CC0 (no attribution needed) instrumental track from Openverse and download it. usage: cc0_music.py "<query>" out.mp3"""
import sys, json, urllib.request, urllib.parse
q, out = sys.argv[1], sys.argv[2]
hdr = {"User-Agent": "junglejuggle-research/1.0"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=hdr), timeout=30).read()
picked = None
for qq in [q, "lofi", "chill beat", "upbeat electronic"]:
    u = "https://api.openverse.org/v1/audio/?" + urllib.parse.urlencode({"q": qq, "license": "cc0", "page_size": 40})
    try: res = json.loads(get(u))["results"]
    except Exception as e: print("api fail", qq, e); continue
    res = [r for r in res if (r.get("duration") or 0) >= 30000 and r.get("url") and r.get("category") in (None, "music")]
    res.sort(key=lambda r: -(r.get("duration") or 0) if (r.get("duration") or 0) < 240000 else 0)
    for r in res:
        try:
            data = get(r["url"])
            if len(data) > 200000:
                open(out, "wb").write(data); picked = r; break
        except Exception as e: print("dl fail", r["url"], e)
    if picked: break
if picked:
    print("PICKED", json.dumps({k: picked.get(k) for k in ("title", "creator", "license", "license_version", "source", "foreign_landing_url", "duration")}, ensure_ascii=False))
else:
    sys.exit(1)
