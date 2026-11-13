"""What do Korean AI-tips accounts post about, which comment keyword do they ask for, which hashtags do they use?

Official Business Discovery API. Commits only derived fields (hashtags, comment keyword, tool names, counts).
Caption first lines are printed to the job log for coding but never written to the repository.
Output: research/out/bench_content.json
"""
import json, os, re, statistics, urllib.parse, urllib.request, datetime as dt

ACCOUNTS = ["gpt_haterz", "adu.aihub", "lazy_owen", "oaiwan.kr", "sebia.ai", "trenddalkak.ai", "grappt_", "ai_newpd",
            "ai.trend.kr", "pickit_.official", "joshproductletter"]
G = "https://graph.facebook.com/v23.0"
TOK, UID = os.environ["IG_ACCESS_TOKEN"], os.environ["IG_USER_ID"]
KST = dt.timezone(dt.timedelta(hours=9))
TOOLS = {"Claude": r"클로드|claude", "ChatGPT": r"챗\s?gpt|chat\s?gpt|gpt|챗지피티", "Gemini": r"제미나이|gemini", "NotebookLM": r"노트북\s?lm|notebooklm",
         "Perplexity": r"퍼플렉시티|perplexity", "Cursor": r"커서|cursor", "Codex": r"코덱스|codex", "Manus": r"마누스|manus", "Genspark": r"젠스파크|genspark",
         "Nano Banana": r"나노\s?바나나|nano\s?banana", "Sora": r"소라|sora", "Veo": r"\bveo\b|비오3", "Midjourney": r"미드저니|midjourney", "Higgsfield": r"higgsfield|힉스필드",
         "Notion": r"노션|notion", "n8n": r"n8n", "Make": r"\bmake\b", "Canva": r"캔바|canva", "Excel": r"엑셀|excel", "PPT": r"ppt|피피티|파워포인트|슬라이드",
         "Kling": r"클링|kling", "Suno": r"수노|suno", "Grok": r"그록|grok", "Copilot": r"코파일럿|copilot", "Antigravity": r"안티그래비티|antigravity", "Obsidian": r"옵시디언|obsidian"}
KW = [r"댓글(?:에|로|창에)?\s*[\"'“‘「『\[]([^\"'”’」』\]]{1,20})[\"'”’」』\]]", r"[\"'“‘「『\[]([^\"'”’」』\]]{1,20})[\"'”’」』\]]\s*(?:이?라고|라고)?\s*댓글",
      r"댓글(?:에|로)?\s*([가-힣A-Za-z0-9]{1,12})\s*(?:남기|달아|적어|써)"]


def get(params):
    params["access_token"] = TOK
    with urllib.request.urlopen(f"{G}/{UID}?" + urllib.parse.urlencode(params), timeout=40) as r:
        return json.load(r)


out = {"generated_at": dt.datetime.now(KST).isoformat(), "accounts": {}}
for u in ACCOUNTS:
    try:
        d = get({"fields": f"business_discovery.username({u}){{followers_count,media.limit(50){{caption,timestamp,media_product_type,like_count,comments_count}}}}"})["business_discovery"]
    except Exception as e:
        out["accounts"][u] = {"error": str(e)[:200]}; continue
    rows = []
    for m in d.get("media", {}).get("data", []):
        cap = m.get("caption") or ""
        tags = re.findall(r"#([^\s#.,!?]+)", cap)
        kw = None
        for p in KW:
            mm = re.search(p, cap)
            if mm: kw = mm.group(1).strip(); break
        low = cap.lower()
        tools = [k for k, p in TOOLS.items() if re.search(p, low)]
        first = cap.strip().split("\n")[0][:60]
        t = dt.datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")).astimezone(KST)
        rows.append({"t": t.strftime("%Y-%m-%d %H:%M"), "type": m.get("media_product_type"), "likes": m.get("like_count") or 0,
                     "comments": m.get("comments_count") or 0, "hashtags": tags, "n_tags": len(tags), "comment_kw": kw,
                     "follow_ask": bool(re.search(r"팔로우", cap)), "dm_ask": bool(re.search(r"DM|디엠|메시지|보내드", cap)),
                     "tools": tools, "cap_len": len(cap)})
        print(f"[{u}] {t:%m-%d} {m.get('media_product_type','')[:4]} 좋{m.get('like_count') or 0} 댓{m.get('comments_count') or 0} kw={kw} | {first}")
    med = statistics.median([r["likes"] + 3 * r["comments"] for r in rows]) if rows else 0
    for r in rows:
        r["x"] = round((r["likes"] + 3 * r["comments"]) / med, 2) if med else None
    out["accounts"][u] = {"followers": d.get("followers_count"), "rows": rows}
os.makedirs("research/out", exist_ok=True)
json.dump(out, open("research/out/bench_content.json", "w"), ensure_ascii=False, indent=1)
