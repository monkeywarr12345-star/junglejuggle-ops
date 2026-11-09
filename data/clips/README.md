# 클립 트랙 기록 (CLAUDE.md '클립 트랙')

- `ledger.json`: 게시한 클립 릴스 한 건당 한 줄.
  `{"reel": "<content id>", "posted_at": "2026-11-10T07:30:00+09:00", "grade": "B|C", "creator": "@handle", "platform": "TikTok", "url": "<원본 링크>", "permission": "<B: 이용 조건 페이지 주소 / C: none>", "status": "live|removed", "note": ""}`
  caption_check.py가 이 파일로 이번 달 C등급 개수(월 9개 한도)를 센다. 삭제 요청·신고가 오면 status를 removed로 바꾸고 creator를 blocked.json에 넣는다.
- `candidates.json`: 클립 발굴 작업이 채우는 후보. `{"found_at", "url", "creator", "platform", "what": "무슨 영상", "money_angle": "돈 각도 한 줄", "score": 0-10, "grade_possible": "B|C", "license_page": "B일 때", "status": "new|file_ready|used|expired|rejected"}`
- `blocked.json`: 삭제 요청·거절한 원작자(다시 쓰지 않음).
- 영상 파일: B등급은 Actions가 공식 주소에서 받아 `clips/`에 둔다(커밋 안 함). C등급 파일은 사용자가 `clips/inbox/`에 올린 것만 쓴다(틱톡·인스타 영상을 스크립트로 내려받지 않음 — 플랫폼 약관).
