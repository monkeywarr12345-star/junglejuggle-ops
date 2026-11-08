# 정글저글(@junglejuggle) 운영 저장소 — Claude 작업 규칙

이 저장소는 인스타그램 경제·트렌드 매거진 '정글저글'의 제작·게시 시스템이다.
전체 운영 원칙(역할, 벤치마킹, 7인 검토, 금지사항)은 Claude 문서
'인스타 자동 운영 시스템 구축 프롬프트'(https://claude.ai/artifact/Y57zMSobkk7fv8CEXJX2sg)를 따른다.
현재 적용 중인 제작 규칙은 `playbook/playbook.md`, 결정 기록은 `playbook/decisions.md`에 있다.

## 구조
- 게시: GitHub Actions `publish.yml`이 5분마다(GitHub 예약 실행은 자주 밀리므로) `queue/*.json` 중 `publish_at`이 지난 항목을 게시하고 `posted/`·`failed/`로 옮긴다. queue에 push하면 즉시 한 번 더 돈다.
- 수집: `collect.yml`이 매일 23:13 KST 우리 게시물 인사이트를 `data/insights/`에, 매일 05:23 KST 경쟁 계정 최신 게시물을 `data/benchmark/daily/`에, 매주 일요일 22:47 KST 경쟁 계정 전체(ekke.now 최대 1,000개·나머지 약 100개)를 `data/benchmark/<날짜>/`에 저장한다. 남의 캡션은 뼈대만, 표지는 OCR·시각 특징만 저장한다(원문·원본 이미지 저장 금지). 벤치마킹 방법은 `playbook/benchmark_method.md`.
- 주간 회고: 월요일 02:47 KST 예약 작업이 벤치마크 코딩·분석·playbook 반영을 끝내서 06:17 아침 제작부터 적용된다.
- 제작: Claude 예약 작업이 이 저장소를 clone해서 콘텐츠를 만들고 queue에 넣는다. (Claude 작업 환경에서는 Instagram API에 접속할 수 없다.)

## 제작 실행 순서 (예약 작업 1회)
1. `git pull`. `failed/`에 새 파일이 있으면 원인을 읽고 고칠 수 있으면 고쳐서 queue에 다시 넣는다.
2. `playbook/playbook.md`와 최근 `data/insights/` 파일을 읽어 오늘 우선할 형식·주제를 정한다. `python3 scripts/bench_analyze.py radar`로 경쟁 계정 24시간 주제 레이더를 본다(2개 계정 이상이 다룬 주제는 시의성 +1, 단 그 계정들과 같은 앵글은 피하고 '내 돈 영향'·'비교' 앵글로). 파일이 없으면 건너뛴다.
3. 이슈 수집: WebSearch(mode standard, 필요하면 extended)로 최근 12시간 경제·소비·기업 뉴스를 찾는다. 기사 페이지를 실제로 열어(WebFetch) 숫자를 확인한다. 검색 스니펫만으로 쓰지 않는다.
4. 점수화: 관심도·공유 가능성·시의성·사실 확인 가능성 각 5점. 가장 높은 것부터 그날 편성 슬롯에 배정한다.
5. 콘텐츠 작성: `content/<YYYY-MM-DD>-<slug>.json`(카드 스펙)과 `.caption.txt`. 스펙에 `benchmark_method.md` 기준표와 같은 `"codes": {"topic_major","angle","hook_cover","hook_first","structure","devices"...}`를 넣는다(벤치마크와 같은 잣대로 성과 비교). 모든 숫자는 서로 다른 두 출처로 교차 확인하고, 확인 못 한 숫자는 빼거나 '~로 알려졌다'가 아니라 아예 쓰지 않는다.
6. 렌더:
   - 그래픽 카드: `python3 scripts/render.py content/<id>.json media/<id>` (JPEG 1080x1350).
   - 실사 사진 표지: 이 환경은 이미지를 내려받을 수 없으므로 GitHub Actions가 사진을 찾아 받아 렌더한다. 스펙에 `"render_in_actions": true`를 넣고 표지를 `{"t":"photo_cover","photo":{"urls":["<공식 보도자료·korea.kr 등 직접 확인한 사진 주소>"],"query":"<영문 검색어>","queries":["<대체 검색어>", ...]},"title":"...","kw":"...","bubble":"한마디(선택)","credit":"urls 사진의 출처"}`로 쓴 뒤 push한다. Actions는 urls를 순서대로 시도하고, 안 되면 검색어마다 Unsplash → Pexels → Pixabay(키 등록된 것만) → Openverse → Wikimedia Commons 순으로 상업 이용·편집 가능한 사진을 찾는다(특정 소스만 쓰려면 photo에 `"sources":["wikimedia"]`처럼 지정; 실제 기업 건물·장소처럼 고유한 대상은 wikimedia가 잘 맞음). 검색어는 영어로 구체적인 사물·장면 2~4개(예: "semiconductor wafer", "seoul stock exchange", "supermarket shelf")를 넣는다. 크레딧은 자동으로 채워지고 `media/<id>/src/credits.json`에 라이선스가 남는다. 3~5분 뒤 `git pull`해서 `media/<id>/01.jpg`를 Read로 열어 사진이 주제와 맞는지 확인한다(기다릴 때는 Bash run_in_background로 git fetch를 20초 간격으로 반복). `src/photo_fallback.txt`가 있으면 사진을 못 찾아 그래픽 배경으로 렌더된 것이니 검색어를 바꿔 한 번 더 push하고, 그래도 안 되면 그래픽 표지로 게시한다. 사진이 주제와 안 맞거나, 인물 얼굴이 크게 나오거나, 주제와 무관한 브랜드 로고(카드사·제조사 등)가 크게 보이면 검색어를 바꾼다(스톡 라이선스도 상표 노출로 보증 오해를 주는 사용은 금지). `src/error.txt`는 렌더 자체 오류다.
   - 사진 고르기 우선순위: (1) 기업·기관 공식 보도자료·뉴스룸 사진 (2) 정책브리핑(korea.kr) 등 공공누리 1유형 (3) 미국 정부 저작물 → 이 셋은 페이지를 WebFetch로 열어 라이선스를 확인하고 `urls`에 넣는다 (Unsplash 사진을 직접 고를 때는 `https://images.unsplash.com/photo-...` 원본 주소에 `?w=1600&q=85&fm=jpg`; `/download` 주소는 401) (4) 나머지는 `query`/`queries` 자동 검색에 맡긴다. 기사 사진, 방송 캡처, 핀터레스트, 연예인·인물 사진 무단 사용, 실존 인물 AI 합성은 금지.
   - 릴스(v3 디자인): 스펙 형식은 `scripts/make_reel.py` 상단 주석. 장면 유형 hook/stat/list/text/cta, 첫 장면은 반드시 `"t":"hook"` + 실사 사진(`"photo":{"query":...,"queries":[...]}`)이고 `"render_in_actions": true`로 push해서 Actions가 사진을 찾아 렌더한다(사진 없는 릴스만 로컬에서 `python3 scripts/make_reel.py content/<id>.reel.json media/<id>/reel.mp4`). 문구는 짧게: title 2줄 이내(한 줄 10자 안팎), sub/lines는 한 줄 22자 안팎, 장면당 3~4초, 전체 18~25초. 숫자는 big에 넣으면 카운트업되고 -는 파랑, +는 빨강(국내 증시 관례). 화면 확대는 배경 사진에만 적용되고 글자는 움직이지 않는다. 같은 장면 유형을 3번 연속 쓰지 않는다. 배경음은 기본값 `"music":{"auto":"upbeat"|"tense"|"chill"}`: 매주 자동 갱신되는 외부 무료 음원 라이브러리(music/library, Jamendo 이번 주 인기곡·신곡 + Openverse, CC0/CC BY/CC BY-SA만)에서 그 분위기 곡 중 가장 오래 안 쓴 곡을 골라 같은 곡이 연달아 나오지 않게 한다(최근 12개 릴스 안 재사용 금지, music/usage.json에 기록). 곡이 정해지면 `media/<id>/music_credit.txt`가 생기는데, 그 한 줄을 캡션 출처 아래에 반드시 그대로 넣는다(CC BY 조건). 라이브러리가 비어 있으면 자체 제작 음악으로 자동 대체된다(크레딧 불필요). 급락·논란 이슈는 tense, 소비·트렌드는 upbeat, 회고·요약은 chill. 새 곡을 바로 받고 싶으면 `music/refresh.request`에 현재 시각을 써서 push하면 music.yml이 즉시 갱신한다(평소엔 매주 일요일 03:37 KST). `{"mood":...}`는 자체 제작 음악, `{"file":"music/library/..."}`는 특정 곡 지정.
   - 피드 음악: 캐러셀은 카드 이미지를 30초 영상 슬라이드로 만들어 게시한다(슬라이드마다 같은 곡을 5초씩 뒤에서 시작해 보통 속도로 넘기면 곡이 이어지게 하고, 읽는 동안 반복·끊김이 없게 함. 7초 슬라이드는 반복 재생 때문에 음악이 끊겨 폐기)(인스타 앱 음악은 API로 못 붙임). 로컬 렌더 후 `python3 scripts/make_feed_video.py content/<id>.json media/<id>`(Actions 렌더는 자동), 출력된 `[{"video":"media/<id>/v01.mp4"},...]`를 queue의 items로 쓴다. 스펙의 `"music":{"auto":"upbeat"|"tense"|"chill"}`로 분위기 지정(기본 upbeat). `media/<id>/music_credit.txt` 한 줄을 캡션에 넣는다. 스토리는 표지 이미지 그대로.
   - 결과 이미지는 Read로 직접 열어 글자 잘림·겹침을 확인하고, 릴스는 ffmpeg로 장면마다 프레임을 뽑아 한 장에 모아 확인한다(첫 장면 실사 사진, 문구가 가운데 한 덩어리로 모여 있는지, 하단 430px 안에 글자가 없는지, 상단 진행 바가 장면마다 한 칸씩 넘어가는지, 2번째 장면 이후에도 단어·숫자 애니메이션이 움직이는지).
   - 캡션 패턴 검사: queue에 넣기 전 `python3 scripts/caption_check.py content/<id>.caption.txt content/<id>.json`(릴스는 .reel.json)을 돌려 PASS가 나와야 한다. 최근 게시물에서 쓴 반응어(ㄷㄷ 등)·비슷한 첫 줄·비슷한 댓글 유도 문구는 FAIL이니 다른 표현으로 바꾼다.
7. 검토: 서로 결과를 보지 않는 별도 에이전트(Agent 도구)에게 7인 검토(편집장, 팩트체커, 법무·저작권, 아트디렉터, 데이터 분석가, 그로스 마케터, 독자 대표)를 맡긴다. 팩트체커와 법무 FAIL은 반드시 고치고 재검토한다. 두 번 연속 FAIL이면 폐기하고 `playbook/decisions.md`에 사유를 남긴다.
8. queue 등록: `queue/<YYYYMMDD-HHMM>-<slug>.json` — 형식은 `scripts/publish.py` 상단 주석 참고. 캐러셀은 `{"type":"carousel","items":[{"image":"media/<id>/01.jpg"},...],"caption":"...","publish_at":"2026-11-09T07:30:00+09:00"}`. 새 피드 게시물마다 표지 이미지를 스토리로도 5분 뒤에 1개 넣는다.
9. 커밋·푸시: 커밋 메시지에 무엇을 언제 게시하는지 적고 `git pull --rebase` 후 push. 실패하면 한 번만 재시도.
10. 운영 로그: `playbook/log/<YYYY-MM-DD>.md`에 이번 실행에서 만든 것, 고른 이유, 버린 후보와 이유를 3~6줄로 추가한다.

## 속보 감시 (예약 작업, 매시간 08~23시 KST)
1. `git pull`. `data/breaking/seen.json`(이미 다룬 속보 목록)과 오늘 `posted/`·`queue/`를 읽는다.
2. WebSearch(mode extended)로 최근 90분 안의 경제 속보를 찾는다: 코스피·코스닥·환율·미 증시 급변(지수 ±2% 이상, 서킷브레이커·사이드카, 환율 하루 ±15원 이상), 기준금리·세금·부동산 대책 발표, 대기업 대형 발표(합병·대규모 투자·리콜·실적 쇼크), 생활물가·소비 관련 화제(가격 인상·품절 대란). 기사 2곳 이상을 열어 사실을 확인한다.
3. 게시 기준(모두 충족): 공유될 만한 파급력, 서로 다른 두 출처로 숫자 확인, seen.json과 오늘 게시물에 없는 내용, 오늘 속보 게시가 2개 미만, 다음 정규 슬롯까지 45분 넘게 남음(45분 이내면 그 슬롯 제작물로 넘기도록 seen.json에 `"fold_into": "<슬롯>"`으로 기록하고 끝냄). 하나라도 안 맞으면 아무것도 만들지 않고 seen.json만 갱신하고 끝낸다(평소에는 대부분 이렇게 끝나는 게 정상).
4. 제작: '속보 카드' 2장 캐러셀(1장: 실사 사진 표지 `photo_cover`에 `"tag": "속보 · HH:MM"`과 결론 숫자, 2장: 무슨 일·왜·내 돈에 미치는 영향 3줄 + 출처) 또는 장 중 급변이면 12~18초 릴스(hook 실사 사진 + stat 1~2개 + cta). 렌더·피드 음악·캡션 검사 규칙은 위 6번과 같다. `"render_in_actions": true`로 push해서 사진을 받는다.
5. 빠른 검토: 7인 검토 대신 팩트체커·법무 2명을 별도 에이전트로 동시에 돌린다(속도 우선). 둘 다 PASS일 때만 queue에 넣고, publish_at은 지금 시각(+2분)으로 한다. 스토리는 5분 뒤 1개.
6. seen.json에 제목·핵심 숫자·출처·처리 결과(게시/보류/슬롯 이관)를 추가하고, 운영 로그에 한 줄 남기고, 커밋·push한다.
7. Instagram이 차단 상태(최근 queue 항목 `_deferred`에 'API access blocked')면 새로 만들지 않고 끝낸다.

## 편성 (KST, 초기값 — playbook.md가 우선)
- 07:30 밤사이 돈 뉴스(캐러셀: 목록 표지 + 항목당 1장 + 마무리) / 10:00 이슈 1개 카드
- 12:30 릴스(순위·비교 숫자형 또는 발언 요약) / 15:30 기업 가계부(주 2회, DART 공시) 또는 물가 체감·퀴즈
- 19:00 이슈 1개 카드 / 21:00 릴스(그날 가장 반응 큰 이슈)
- 일요일 19:00 주간 돈 뉴스 5

## 반드시 지킬 것
- 사용자에게 보내는 모든 메시지·보고·알림, 운영 로그는 반드시 한국어로 쓴다(코드·파일명·커밋 메시지 제외).
- 원문 복사 금지, 직접 재작성하고 출처를 캡션과 카드에 적는다. 기사 사진·방송 캡처·핀터레스트 이미지·실존 인물 AI 합성 금지.
- 이미지·영상은 직접 만든 그래픽, 공식 보도자료, 공공누리 1유형(정책브리핑·KTV), 미국 정부 저작물, 무료 상업 이용 스톡만. 편성 중 하루 2개 이상은 실사 사진 표지로 만든다(이슈 1개 카드 슬롯 우선).
- 릴스 음악은 music/library의 외부 무료 음원(라이선스·크레딧 기록됨) 또는 자체 제작 음악만. 상업 음원(K-pop 등 인기 가요)은 API로 쓸 수 없다. 인스타 앱 음악은 API로 붙일 수 없으므로 사용자가 앱에서 직접 붙이는 경우에만 쓴다.
- 투자 권유 금지(매수·매도 언급 금지, '정보 제공 목적' 표기). 정치는 사실만, 편들지 않는다. 미확인 루머·사생활 금지.
- 말투: 음슴체(~함/~임) + 가벼운 반응어, 독자 호칭은 '정글러님들'. 합쇼체·홍보 위주 게시물 금지. 반응어는 게시물마다 다르게(ㄷㄷ만 반복 금지, 최근 6개 게시물과 겹치지 않게), 반응어 없이 숫자·질문으로 여는 첫 줄도 섞는다. 댓글 유도 문구도 매번 형식을 바꾼다(고르기, 숫자 맞히기, 경험 묻기, 친구 태그 등).
- 해시태그: 2주간 A/B 실험 중(playbook.md 참고).
- 다른 계정 사칭·디자인 복제, 스크래핑, 자동 팔로우·좋아요·남의 게시물 댓글, 팔로워 구매 금지. 유료 결제 금지.
- 게시물 삭제 등 되돌리기 어려운 일은 하지 않고, 필요하면 운영 로그에 '사용자 확인 필요'로 남긴다.
