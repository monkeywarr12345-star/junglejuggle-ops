# 정글 GCC AI 릴스 제작 가이드 (예약 제작 작업이 그대로 따른다)

운영안: https://claude.ai/artifact/2fJWEiod1pwo8FfREqY3P9 ('운영안' 탭). 규칙 요약은 저장소 루트 CLAUDE.md 맨 위 'AI 실사용 릴스' 절.
사용자에게 보내는 모든 글은 한국어(해요체). 게시는 사용자가 앱에서 직접 한다 — queue에 넣지 않는다.

## 폴더
- **현재 제작 틀(2026-11-13 사용자 결정): v6 '정글 탐험' 스타일** — `ai/reels/2026-11-13-claude-setup/`(index.html·build.py·mascot.js·cover.html·vendor/three)를 복사해 시작한다. 3D 정글이(그루터기 위), 초록 숲 배경·흔들리는 잎·반딧불이, 상단 '🌿 탐험 진행' 길, 노란 테이프 크림 종이 카드, 노란 형광펜 강조 자막, 큰 잎이 쓸고 가는 장면 전환. 목소리 `supertonic M1 @1.3`(남자). 움직임은 이 틀 정도가 기준이다 — 카메라 펀치 줌·화면 흔들림·장면마다 회전 같은 강한 효과는 넣지 않는다(2026-11-13 사용자: '너무 정신 사납다', 이전 버전 선택). 아래 v4(`ai/template/`) 설명은 옛 틀 기록이다.
- 배치 규칙(사용자 지시 '글자가 정글이를 가리지 않게'): 자막 띠 y 1110~1300(.w top 1112, .sub top 1246), 카드·목업은 y 300~1080 안, 정글이는 첫 두 장면 y 470~1085(가운데 크게), 나머지는 왼쪽 아래 y 1335~1660(fit() 함수로 화면 박스에 맞춤). 로컬 미리보기 때 scratchpad의 overlap.py처럼 캔버스 알파 박스와 글자 요소의 겹침을 재서 0이어야 한다.
- 표지(사용자 지시: 벤치마크의 마스코트만 나오는 표지 스타일): 릴스 폴더의 `cover.html` — 정글 배경, 위쪽 가운데 도구 아이콘 타일(크림색 둥근 사각형), 가운데 정글이(그루터기, 손 흔들기), 왼쪽 아래 'jungle.gcc ●●●' + 제목 3줄(118px, 핵심어 노란색). 프로필 격자는 가운데 3:4(y 240~1680)만 보이므로 모든 요소를 그 안에. 렌더 작업이 cover.html을 따로 렌더해 cover.jpg로 쓴다.
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
11. Zorcha 자동화: 릴스마다 만들 필요 없다(2026-11-13 사용자 지시 '매일 되게'). zorcha.com에 상시 자동화 '매일 · 모든 릴스 · 아무 댓글 → 팔로우 확인 → 자료실' 하나가 Live다 — ① Any post or reel 켬 ② Any keyword 켬 ③ DM '요청하신 자료예요 🎁 … 맨 위 카드가 방금 보신 릴스 자료예요!' + [자료 열기] → https://junglegcc.github.io/ (자료실 첫 화면) · Opening Message = 모두에게 가는 팔로우 확인('댓글 고마워요! … 자료는 팔로워 전용이에요. @jungle.gcc 팔로우하셨다면 아래 버튼을 눌러 주세요! 🙏' + [팔로우했어요 ✅]) — Zorcha의 Ask to follow는 팔로워가 아닌 사람에게만 나오므로, 이미 팔로우한 사람도 항상 확인 단계를 거치게 첫 메시지를 확인 메시지로 씀(2026-11-13 사용자 지시) · Ask to follow(팔로워가 아니면 '아직 팔로우가 확인되지 않았어요 😢 … 다시 눌러 주세요!' + Visit Profile + [팔로우했어요 ✅], 실제 팔로우가 확인될 때까지 자료가 안 감) · 이미 팔로우한 사람이 다른 릴스에 다시 댓글을 달면 Zorcha가 첫 메시지·팔로우 요청을 건너뛰고 자료 DM만 보낼 수 있다(무료 플랜은 DM 안에 버튼 단계를 더 넣을 수 없음 — 'Add Message'는 유료). 그래서 자료실 모든 페이지가 열릴 때마다 '@jungle.gcc 팔로우하셨나요?' 확인 화면을 띄운다(`assets/gate.js`, 새 페이지에도 `<script src="../../assets/gate.js"></script>`를 site.css 다음 줄에 꼭 넣는다) · 공개 답글 3개. 그래서 매 릴스에서 할 일은 자료실 첫 화면 목록 맨 위에 새 카드를 넣는 것뿐이다(9단계). dm.json은 기록용으로 keyword·card.url만 쓰고 `"zorcha": "always-on"`. 팔로우 확인 시험은 jungle.gcc를 팔로우하지 않은 계정으로 해야 한다(이미 팔로우 중인 계정은 확인 단계가 건너뛰어짐).
12. 검토: 서로 결과를 보지 않는 별도 에이전트 2명 — 팩트체커(기능·메뉴·요금·숫자가 공식 문서와 맞는지), 그로스(0초 훅·키워드 일치·마지막 장면·캡션 첫 줄). FAIL은 고쳐서 다시.
13. 기록·알림: topics.json status done(게시 예정 시각), `playbook/predictions/`의 예측표에 한 줄(예측 도달·저장·팔로우·키워드 댓글), `playbook/log/<날짜>.md` 한 줄, 커밋·push. PushNotification(영상은 항상 두 버전 다):
    "<요일> <시각> 릴스 준비 완료: <제목>\n영상(음악 있음): https://github.com/monkeywarr12345-star/junglejuggle-ops/raw/main/media/ai/<id>/reel.mp4\n영상(음악 없음): https://github.com/monkeywarr12345-star/junglejuggle-ops/raw/main/media/ai/<id>/reel_nomusic.mp4\n표지: …/cover.jpg (올릴 때 '커버 편집 → 카메라 롤에서 추가'로 이 jpg를 꼭 고르기 — 안 고르면 인스타가 중간 장면을 표지로 씀)\n올릴 때 '고급 설정 → AI 레이블(AI 정보)' 켜기 — 내레이션이 AI 합성 음성이라 Meta 공개 대상\n캡션: …/ai/reels/<id>/caption.txt\n자료: https://junglegcc.github.io/p/<slug>/\nDM 자동화: 완료 / 직접 필요".

## 준비 마감
18·21시 게시분은 같은 날 12:00, 11시 게시분은 같은 날 08:00까지 알림까지 끝낸다. 마감이 다가오면 다듬기보다 완성을 우선한다.
