# 정글저글(@junglejuggle) 운영 저장소 — Claude 작업 규칙

이 저장소는 인스타그램 경제·트렌드 매거진 '정글저글'의 제작·게시 시스템이다.
전체 운영 원칙(역할, 벤치마킹, 7인 검토, 금지사항)은 Claude 문서
'인스타 자동 운영 시스템 구축 프롬프트'(https://claude.ai/artifact/Y57zMSobkk7fv8CEXJX2sg)를 따른다.
현재 적용 중인 제작 규칙은 `playbook/playbook.md`, 결정 기록은 `playbook/decisions.md`에 있다.

## 구조
- 게시: GitHub Actions `publish.yml`이 30분마다 `queue/*.json` 중 `publish_at`이 지난 항목을 게시하고 `posted/`·`failed/`로 옮긴다. queue에 push하면 즉시 한 번 더 돈다.
- 수집: `collect.yml`이 매일 23:13 KST 우리 게시물 인사이트를 `data/insights/`에, 매주 월요일 05:43 KST 벤치마크 계정 게시물을 `data/benchmark/`에 저장한다.
- 제작: Claude 예약 작업이 이 저장소를 clone해서 콘텐츠를 만들고 queue에 넣는다. (Claude 작업 환경에서는 Instagram API에 접속할 수 없다.)

## 제작 실행 순서 (예약 작업 1회)
1. `git pull`. `failed/`에 새 파일이 있으면 원인을 읽고 고칠 수 있으면 고쳐서 queue에 다시 넣는다.
2. `playbook/playbook.md`와 최근 `data/insights/` 파일을 읽어 오늘 우선할 형식·주제를 정한다.
3. 이슈 수집: WebSearch(mode standard, 필요하면 extended)로 최근 12시간 경제·소비·기업 뉴스를 찾는다. 기사 페이지를 실제로 열어(WebFetch) 숫자를 확인한다. 검색 스니펫만으로 쓰지 않는다.
4. 점수화: 관심도·공유 가능성·시의성·사실 확인 가능성 각 5점. 가장 높은 것부터 그날 편성 슬롯에 배정한다.
5. 콘텐츠 작성: `content/<YYYY-MM-DD>-<slug>.json`(카드 스펙)과 `.caption.txt`. 모든 숫자는 서로 다른 두 출처로 교차 확인하고, 확인 못 한 숫자는 빼거나 '~로 알려졌다'가 아니라 아예 쓰지 않는다.
6. 렌더: `python3 scripts/render.py content/<id>.json media/<id>` (카드, JPEG 1080x1350). 릴스는 `python3 scripts/make_reel.py content/<id>.reel.json media/<id>/reel.mp4`. 결과 이미지를 Read로 직접 열어 글자 잘림·겹침을 확인한다.
7. 검토: 서로 결과를 보지 않는 별도 에이전트(Agent 도구)에게 7인 검토(편집장, 팩트체커, 법무·저작권, 아트디렉터, 데이터 분석가, 그로스 마케터, 독자 대표)를 맡긴다. 팩트체커와 법무 FAIL은 반드시 고치고 재검토한다. 두 번 연속 FAIL이면 폐기하고 `playbook/decisions.md`에 사유를 남긴다.
8. queue 등록: `queue/<YYYYMMDD-HHMM>-<slug>.json` — 형식은 `scripts/publish.py` 상단 주석 참고. 캐러셀은 `{"type":"carousel","items":[{"image":"media/<id>/01.jpg"},...],"caption":"...","publish_at":"2026-11-09T07:30:00+09:00"}`. 새 피드 게시물마다 표지 이미지를 스토리로도 5분 뒤에 1개 넣는다.
9. 커밋·푸시: 커밋 메시지에 무엇을 언제 게시하는지 적고 `git pull --rebase` 후 push. 실패하면 한 번만 재시도.
10. 운영 로그: `playbook/log/<YYYY-MM-DD>.md`에 이번 실행에서 만든 것, 고른 이유, 버린 후보와 이유를 3~6줄로 추가한다.

## 편성 (KST, 초기값 — playbook.md가 우선)
- 07:30 밤사이 돈 뉴스(캐러셀: 목록 표지 + 항목당 1장 + 마무리) / 10:00 이슈 1개 카드
- 12:30 릴스(순위·비교 숫자형 또는 발언 요약) / 15:30 기업 가계부(주 2회, DART 공시) 또는 물가 체감·퀴즈
- 19:00 이슈 1개 카드 / 21:00 릴스(그날 가장 반응 큰 이슈)
- 일요일 19:00 주간 돈 뉴스 5

## 반드시 지킬 것
- 원문 복사 금지, 직접 재작성하고 출처를 캡션과 카드에 적는다. 기사 사진·방송 캡처·핀터레스트 이미지·실존 인물 AI 합성 금지.
- 이미지·영상은 직접 만든 그래픽, 공식 보도자료, 공공누리 1유형(정책브리핑·KTV), 미국 정부 저작물, 무료 상업 이용 스톡만.
- 투자 권유 금지(매수·매도 언급 금지, '정보 제공 목적' 표기). 정치는 사실만, 편들지 않는다. 미확인 루머·사생활 금지.
- 말투: 음슴체(~함/~임) + 가벼운 반응어, 독자 호칭은 '정글러님들'. 합쇼체·홍보 위주 게시물 금지.
- 해시태그: 2주간 A/B 실험 중(playbook.md 참고).
- 다른 계정 사칭·디자인 복제, 스크래핑, 자동 팔로우·좋아요·남의 게시물 댓글, 팔로워 구매 금지. 유료 결제 금지.
- 게시물 삭제 등 되돌리기 어려운 일은 하지 않고, 필요하면 운영 로그에 '사용자 확인 필요'로 남긴다.
