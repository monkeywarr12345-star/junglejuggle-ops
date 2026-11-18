"""Which topics get the biggest response on Korean AI-tips accounts?

Official Business Discovery API, up to ~300 recent posts per account.
Commits only derived fields: counts, date, type, shortcode, first line (60 chars, same as data/study skeleton),
comment keyword, tool names and the vocabulary terms that appear in the caption (no caption text).
Caption heads are printed to the job log for manual coding checks but never written to the repository.
Output: research/out/bench_topics.json
"""
import json, os, re, time, urllib.parse, urllib.request, datetime as dt

ACCOUNTS = ["pickit_.official", "sebia.ai", "adu.aihub", "gpt_haterz", "joshproductletter", "reborn.ax", "grappt_", "work__zero",
            "ai_dori_", "ai_newpd", "ai.trend.kr", "trenddalkak.ai", "ai.brief.kr", "mktg.with.ai", "prompt_what", "lazy_owen",
            "roy.branding", "theaigeekk", "mart_eting", "oaiwan.kr"]
PAGES = 6
G = "https://graph.facebook.com/v23.0"
TOK, UID = os.environ["IG_ACCESS_TOKEN"], os.environ["IG_USER_ID"]
KST = dt.timezone(dt.timedelta(hours=9))

# vocabulary: term -> regex (lowercased caption). Coding into topics happens offline from these terms.
VOCAB = {
 # tools
 "claude": r"클로드|claude", "chatgpt": r"챗\s?gpt|chat\s?gpt|챗지피티|\bgpt", "gemini": r"제미나이|gemini|제미니", "notebooklm": r"노트북\s?lm|notebooklm",
 "perplexity": r"퍼플렉시티|perplexity", "cursor": r"커서|cursor", "codex": r"코덱스|codex", "claude_code": r"클로드\s?코드|claude\s?code",
 "cowork": r"코워크|cowork", "manus": r"마누스|manus", "genspark": r"젠스파크|genspark", "nanobanana": r"나노\s?바나나|nano\s?banana",
 "sora": r"소라\b|sora", "veo": r"\bveo|비오\s?3", "midjourney": r"미드저니|midjourney", "higgsfield": r"higgsfield|힉스필드", "kling": r"클링|kling",
 "suno": r"수노|suno", "grok": r"그록|grok", "copilot": r"코파일럿|copilot", "antigravity": r"안티그래비티|antigravity", "obsidian": r"옵시디언|obsidian",
 "notion": r"노션|notion", "n8n": r"n8n", "canva": r"캔바|canva", "capcut": r"캡컷|capcut", "figma": r"피그마|figma", "google": r"구글|google",
 "openai": r"오픈ai|openai|오픈에이아이", "anthropic": r"앤트로픽|anthropic", "fable": r"페이블|fable", "mythos": r"미토스|mythos", "seedance": r"시댄스|seedance",
 # features / mechanics
 "skill": r"스킬|skill", "mcp": r"\bmcp", "plugin": r"플러그인|plugin|확장\s?프로그램|extension", "agent": r"에이전트|agent", "automation": r"자동화|자동으로|automation",
 "connect": r"연결|연동", "setting": r"설정|세팅|setting", "hidden": r"숨은|숨겨진|몰랐던|모르는|아무도\s?모르|비밀", "prompt": r"프롬프트|prompt",
 "oneline": r"한\s?줄|한마디|한\s?문장|한\s?단어", "command": r"명령어|코드\s?\d|단축키|비밀\s?코드", "memory": r"메모리|기억|memory", "project": r"프로젝트|project",
 "free": r"무료|공짜|0원|free", "limit": r"한도|사용량|토큰", "paid": r"유료|구독|요금|결제|플랜", "update": r"업데이트|새\s?기능|신기능|출시|공개|발표|런칭|등장",
 "new_model": r"신모델|새\s?모델|모델\s?출시|5\.\d|o\d\b|gpt-?\d", "compare": r"\bvs\b|비교|차이|대결|뭐가\s?나아|어떤\s?게\s?나아",
 "combo": r"조합|같이\s?쓰|합체|팀|함께\s?쓰", "install": r"설치|깔|다운로드|install", "github": r"깃허브|github|오픈\s?소스|open\s?source",
 # outputs / use cases
 "video": r"영상|비디오|video|쇼츠|릴스\s?만들|애니메이션|애니|모션", "image": r"이미지|사진|그림|일러스트|image", "profile_photo": r"프로필|증명사진|셀카",
 "webtoon": r"웹툰|만화|캐릭터", "edit_photo": r"보정|합성|누끼|배경\s?(제거|바꾸)", "ppt": r"ppt|피피티|파워포인트|슬라이드|발표\s?자료", "excel": r"엑셀|excel|스프레드시트|시트",
 "doc": r"보고서|문서|기획서|pdf|요약", "meeting": r"회의|미팅|회의록", "email": r"메일|이메일|gmail|지메일", "writing": r"글쓰기|글을|블로그|카피|문장|원고|글\s?티|ai\s?티",
 "coding": r"코딩|개발|앱\s?만들|웹사이트|홈페이지|바이브\s?코딩|vibe|웹\s?앱|서비스\s?만들", "game": r"게임|game", "design": r"디자인|design|ui|ux|로고|폰트|상세\s?페이지",
 "landing": r"랜딩|상세페이지|홈페이지", "research": r"리서치|조사|논문|자료\s?조사|딥\s?리서치|검색", "study": r"공부|학습법|시험|수능|강의|영어|외국어|번역",
 "stock": r"주식|투자|종목|코인|차트|매매|트레이딩|etf|펀드", "money": r"수익|부업|돈\s?버|월\s?\d+\s?(만|천)|매출|창업|사업", "marketing": r"마케팅|광고|브랜딩|인스타|릴스|유튜브|sns|콘텐츠|팔로워",
 "job": r"이력서|자소서|자기소개서|면접|취업|이직|채용", "work": r"업무|회사|직장|직장인|야근|퇴근|일잘러|칼퇴", "productivity": r"생산성|시간\s?절약|효율|10배|시간을\s?아",
 "travel": r"여행|맛집|일정", "food": r"요리|레시피|식단|다이어트", "health": r"건강|운동|병원|약", "parent": r"육아|아이|아기|엄마|부모", "love": r"연애|소개팅|커플|결혼|선물|기념일",
 "music": r"노래|음악|작곡|bgm|music", "voice": r"목소리|음성|더빙|tts|보이스", "privacy": r"개인정보|유출|보안|해킹|학습에\s?쓰|학습\s?데이터|프라이버시|privacy",
 "security_warn": r"위험|조심|주의|경고|하지\s?마", "news": r"뉴스|소식|속보|이번\s?주", "trend_viral": r"화제|난리|바이럴|떡상|미쳤|역대급|충격|대박",
 "hallucination": r"거짓말|환각|할루시|틀린\s?답|헛소리", "sycophancy": r"맞장구|아첨|칭찬만|동의만|반대\s?의견|팩트", "persona": r"페르소나|역할|전문가처럼|expert",
 "chrome": r"크롬|chrome|브라우저", "phone": r"아이폰|갤럭시|스마트폰|폰으로|휴대폰|모바일", "mac_pc": r"맥북|윈도우|pc|컴퓨터|노트북으로",
 "kakao": r"카톡|카카오", "naver": r"네이버|naver", "map_local": r"지도|부동산|청약|세금|연말정산|정부|지원금",
 # devices
 "list_n": r"\d+\s?(가지|개|선|단계|종|스텝)", "save_ask": r"저장", "follow_ask": r"팔로우", "comment_ask": r"댓글", "dm": r"dm|디엠|보내드|보내\s?드",
}
KW = [r"댓글(?:에|로|창에)?\s*[\"'“‘「『\[]([^\"'”’」』\]]{1,20})[\"'”’」』\]]", r"[\"'“‘「『\[]([^\"'”’」』\]]{1,20})[\"'”’」』\]]\s*(?:이?라고|라고)?\s*(?:댓글|남겨|적어)",
      r"댓글(?:에|로)?\s*([가-힣A-Za-z0-9]{1,12})\s*(?:남기|달아|적어|써)"]


def get(params):
    params["access_token"] = TOK
    for i in range(3):
        try:
            with urllib.request.urlopen(f"{G}/{UID}?" + urllib.parse.urlencode(params), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if i == 2 or e.code == 400:
                raise RuntimeError(f"{e.code} {body}")
            time.sleep(15)


out = {"generated_at": dt.datetime.now(KST).isoformat(), "accounts": {}}
FIELDS = "caption,timestamp,media_product_type,media_type,like_count,comments_count,permalink"
for u in ACCOUNTS:
    rows, after, followers, err = [], None, None, None
    for page in range(PAGES):
        media = f"media.limit(50){{{FIELDS}}}" if not after else f"media.after({after}).limit(50){{{FIELDS}}}"
        try:
            d = get({"fields": f"business_discovery.username({u}){{followers_count,media_count,{media}}}"})["business_discovery"]
        except Exception as e:
            err = str(e)[:200]; break
        followers = d.get("followers_count")
        for m in d.get("media", {}).get("data", []):
            cap = m.get("caption") or ""
            low = cap.lower()
            terms = [k for k, p in VOCAB.items() if re.search(p, low)]
            kw = None
            for p in KW:
                mm = re.search(p, cap)
                if mm: kw = mm.group(1).strip(); break
            t = dt.datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")).astimezone(KST)
            first = cap.strip().split("\n")[0][:60]
            sc = (m.get("permalink") or "").rstrip("/").split("/")[-1]
            rows.append({"sc": sc, "t": t.strftime("%Y-%m-%d %H:%M"), "type": m.get("media_product_type"), "mt": m.get("media_type"),
                         "likes": m.get("like_count") or 0, "comments": m.get("comments_count") or 0, "first": first,
                         "kw": kw, "terms": terms, "cap_len": len(cap)})
            head = re.sub(r"\s+", " ", cap)[:140]
            print(f"[{u}] {sc} {t:%y-%m-%d} {str(m.get('media_product_type'))[:4]} L{m.get('like_count') or 0} C{m.get('comments_count') or 0} | {head}")
        after = d.get("media", {}).get("paging", {}).get("cursors", {}).get("after")
        if not after or not d.get("media", {}).get("paging", {}).get("next"):
            break
        time.sleep(2)
    out["accounts"][u] = {"followers": followers, "rows": rows, **({"error": err} if err else {})}
    print(f"== {u}: {len(rows)} posts, followers {followers}, err {err}")
os.makedirs("research/out", exist_ok=True)
json.dump(out, open("research/out/bench_topics.json", "w"), ensure_ascii=False, indent=0)
