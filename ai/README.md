# 정글 GCC AI 릴스 제작 가이드 (예약 제작 작업이 그대로 따른다)

운영안: https://claude.ai/artifact/2fJWEiod1pwo8FfREqY3P9 ('운영안' 탭). 규칙 요약은 저장소 루트 CLAUDE.md 맨 위 'AI 실사용 릴스' 절.
사용자에게 보내는 모든 글은 한국어(해요체). 게시는 사용자가 앱에서 직접 한다 — queue에 넣지 않는다.

## 폴더
- `ai/template/` — 견본 v4 기준 틀(index.html 장면, build.py 대본·타이밍·효과음, voice.txt, music.txt). 새 릴스는 여기서 복사해 시작한다.
- `ai/chars/img0~6.jpg` — 같은 캐릭터(주황 가디건, 안경) 그림. 렌더 때 배경을 지운 컷(cut0·2·3·4·5)이 자동으로 만들어진다. 새 자세가 꼭 필요할 때만 실험 브랜치의 그림 생성 작업으로 추가한다.
- `ai/reels/<YYYY-MM-DD>-<slug>/` — 릴스 1편: index.html, build.py, voice.txt, music.txt, caption.txt, dm.json. push하면 `.github/workflows/ai-reel.yml`이 렌더해서 `media/ai/<id>/`에 reel.mp4(자체 음악)·reel_nomusic.mp4(앱 음악용)·cover.jpg·contact.jpg·timeline.json을 커밋한다(5~10분).
- `ai/topics.json` — 주제 후보표(상태 todo/doing/done, 키워드, 근거).
- 자료실 = 별도 저장소 `junglegcc/junglegcc.github.io`(GitHub Pages, 주소 https://junglegcc.github.io/). add_repo(owner "junglegcc", repo "junglegcc.github.io", access "push") 후 `/home/claude/junglegcc.github.io`에 clone. 릴스마다 그 저장소의 `p/<slug>/index.html`(+ 화면 3장 jpg)을 만들고 루트 `index.html` 목록 맨 위에 카드를 추가해 push한다. ops 저장소의 `docs/`는 옛 주소를 새 주소로 넘기는 안내만 남아 있으니 고치지 않는다.

## 제작 순서 (1회 = 1편)
1. `git pull`. `ai/topics.json`에서 오늘 게시분 주제를 고른다(status todo 중 맨 위. 같은 도구가 3편 연속이면 다음 것). 주간 회고가 바꾼 순서를 따른다.
2. 사실 확인: 그 기능이 지금 실제로 되는지 공식 문서·공식 블로그·도움말을 WebFetch로 열어 확인한다(메뉴 이름, 무료/유료, 모델 이름). 안 되거나 유료 전용이면 화면·캡션에 '유료 플랜'을 표시하거나 다음 주제로 넘긴다.
3. 댓글 키워드: 주제에 맞는 한글 2~3자(예: 세팅, 명령어, PPT). 최근 10편과 겹치지 않게. build.py `KEYWORD`, 마지막 장면, caption.txt 첫 줄, dm.json에 같은 단어.
4. 대본(build.py `LINES`): 18~25초, 문장 9개 안팎, 해요체. 첫 문장은 훅 공식(손해 금액·시간 압축·한 줄 마법·비교·모르면 손해) 중 하나. 마지막 문장은 항상 "팔로우하고 댓글에 ○○, 남기면 프롬프트 전체본 디엠으로 보내드려요."(TTS는 'DM'을 '디엠'으로 써야 바르게 읽음, 자막은 DM). 숫자는 TTS용으로 한글로 풀어 쓰고 자막은 숫자로.
5. 장면(index.html): 문장마다 장면 하나, 1~2초마다 새 요소. 템플릿의 부품을 재사용·변형한다 — 휴대폰 목업(.phone), 맥 창(.win, 빨·노·초 점), 입력창 타이핑(.composer), 결과 표(table.t), 카드 묶음(.pair), 빨간 도장(.stamp), 검은 숫자 배지(.pill), 알림 칩(.noti), 캐릭터(.chr cut0~5), 마지막 팔로우+댓글+DM 장면(#s9). 실제 서비스(ChatGPT·Claude·Gemini) 화면은 그 서비스의 실제 모양(입력창 문구, 로고 색, 모델 표시)에 가깝게 그린다. 0초 프레임에 제목 2줄·자막·캐릭터가 다 보이게 한다. 제목은 y 300 아래(프로필 격자 3:4 안), 자막은 1352px 한 줄.
6. 로컬 확인(선택): build.py를 'none' 목소리로 돌리고 Playwright로 seek해 프레임을 본다. `window.__timelines.main.seek(t)` 뒤에 `; 0`을 붙여야 evaluate가 멈추지 않는다.
7. push → 렌더 기다리기(Monitor/until로 `media/ai/<id>/reel.mp4` 생길 때까지, 최대 20분). contact.jpg를 Read로 열어 겹침·잘림·빈 화면이 없는지 본다. 고치면 다시 push.
8. 캡션(caption.txt): 첫 줄 = 결과 + "💬 팔로우하고 댓글에 '○○' 남기면 프롬프트 전체본 보내드려요". 본문 2줄, 📌 프롬프트 핵심 3개, 🎁 전체본 안내, ℹ️ 무료/유료·예시 표시, 해시태그 정확히 5개(2026-11-13 사용자 결정 — 도구 이름 1~2 + 활용어 1~2 + 주제어 1~2, 매번 조합을 바꿈).
9. 자료 페이지(자료실 저장소): `p/<slug>/index.html`(subscription 페이지 형식: 칩, 제목 2줄 형광펜, 리드 1문장, 따라 하기 3단계 + 영상 화면 3장, 복사 버튼 프롬프트 5개, 팁 2~3개, 팔로우 버튼), 화면 jpg 3장은 reel.mp4에서 ffmpeg로 뽑는다. 루트 `index.html` 목록 맨 위에 카드 추가, 자료실 저장소에 커밋·push(1~2분 뒤 주소가 열리는지 WebFetch로 확인).
10. dm.json(키워드는 영상·캡션의 공개 안내용일 뿐, DM은 모든 댓글에 보냄): keyword, 댓글 답글 3개, 팔로우 확인 문구·버튼, 자료 카드(제목·설명·버튼 '자료 열기'·url=자료 페이지). PC용 링크 줄은 넣지 않는다.
11. Zorcha 자동화: 무료 플랜이라 AI(MCP)로는 못 만든다(2026-11-13 확인). 집 Chrome(Claude in Chrome)으로 zorcha.com에서 dm.json대로 만든다 — 집 컴퓨터를 쓰는 예약 작업이 아직 없으므로(만들기가 막힘, 사용자 확인 대기), 제작 작업은 dm.json을 정확히 쓰고 `"zorcha": "pending"`을 넣은 뒤 알림 끝에 'Zorcha에 넣을 것'을 붙인다. 사용자와 대화 중인 세션이나 집 컴퓨터를 쓰는 작업은 아래 순서로 직접 만든다. dm.json 형식: keyword, keywords_also, comment_replies 3개, opening{text,button}, follow_gate{text: "댓글 고마워요! 팔로우하셨다면 아래 버튼을 눌러 주세요! 🙏", button: "팔로우했어요 ✅"}, dm_text, card{title, subtitle, button: "자료 열기", url}, target "next_post". Zorcha 화면 순서(검증됨): Automations → New Automation → 'DM from Comments' → 이름 → ① Next Post or Reel ② Any keyword 켜기(댓글이면 무엇이든 DM — 2026-11-13 사용자 결정 '우리만의 비밀', 키워드 칸은 비워 둠) ③ DM 문구 + Add Link(제목·주소) → Advanced: Public reply 켜고 영어 기본 답글 3개를 교체, Opening Message 켜고(팔로우 확인에 필수) 문구·버튼 교체, Ask to follow 켜고 문구·'I'm following' 버튼 교체 → Go Live → 목록에서 Live 확인.
12. 검토: 서로 결과를 보지 않는 별도 에이전트 2명 — 팩트체커(기능·메뉴·요금·숫자가 공식 문서와 맞는지), 그로스(0초 훅·키워드 일치·마지막 장면·캡션 첫 줄). FAIL은 고쳐서 다시.
13. 기록·알림: topics.json status done(게시 예정 시각), `playbook/predictions/`의 예측표에 한 줄(예측 도달·저장·팔로우·키워드 댓글), `playbook/log/<날짜>.md` 한 줄, 커밋·push. PushNotification(영상은 항상 두 버전 다):
    "<요일> <시각> 릴스 준비 완료: <제목>\n영상(음악 있음): https://github.com/monkeywarr12345-star/junglejuggle-ops/raw/main/media/ai/<id>/reel.mp4\n영상(음악 없음): https://github.com/monkeywarr12345-star/junglejuggle-ops/raw/main/media/ai/<id>/reel_nomusic.mp4\n표지: …/cover.jpg (올릴 때 '커버 편집 → 카메라 롤에서 추가'로 이 jpg를 꼭 고르기 — 안 고르면 인스타가 중간 장면을 표지로 씀)\n캡션: …/ai/reels/<id>/caption.txt\n자료: https://junglegcc.github.io/p/<slug>/\nDM 자동화: 완료 / 직접 필요".

## 준비 마감
18·21시 게시분은 같은 날 12:00, 11시 게시분은 같은 날 08:00까지 알림까지 끝낸다. 마감이 다가오면 다듬기보다 완성을 우선한다.
