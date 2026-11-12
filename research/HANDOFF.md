# 정글저글 AI 도구 계정 전환 — 작업 인계서 (2026-11-13 00:55 KST)

새 대화(데스크톱 앱, 내 컴퓨터 연결)에서 이어 하기 위한 요약이다. 새 Claude는 이 파일을 먼저 읽고, 필요하면 아래 저장소·문서를 직접 열어 확인한다.

## 0. 새 대화에서 바로 할 일 (지금 막힌 것)

1. **실제 화면 녹화 만들기 (OpenScreen)**
   - 사용자 PC(Windows)에 OpenScreen v2.2.2 설치 파일 `Openscreen.Setup.2.2.2-x64.exe`(171MB, github.com/getopenscreen/openscreen 릴리스)를 받아 둠. 사용자가 받았다고 함. 설치 여부는 확인 필요.
   - Chrome의 Claude 탭 묶음에 ChatGPT 탭(chatgpt.com, 로그아웃 상태)을 열고 입력창에 아래 문장을 **보내지 않은 채** 입력해 둠.
     ```
     카드 내역: 넷플릭스 13,500 / 티빙 13,900 / 유튜브 프리미엄 14,900 / 아이클라우드 4,400 / 구글 원 2,400 / 멜론 10,900 / GS25 4,300 / 스타벅스 6,100 — 매달 반복 결제만 표로 뽑아 줘. 기능이 겹치는 건 표시해 줘.
     ```
     (탭이 닫혔으면 다시 열고 같은 문장을 넣는다. 금액은 예시 데이터.)
   - 할 일: OpenScreen으로 녹화 시작 → ChatGPT 탭에서 Enter → 답(표)이 다 나오면 중지 → 자동 확대(auto zoom) 켜고 mp4로 내보내기(가능하면 세로 9:16 또는 채팅 영역 위주).
   - 결과 mp4를 저장소에 올린다. 사용자 안내로는 `main`의 `clips/inbox/rec1.mp4`(업로드 페이지: github.com/monkeywarr12345-star/junglejuggle-ops/upload/main/clips/inbox). 견본 작업은 실험 브랜치에서 하므로 **실험 브랜치 `research/ai-tools-2026-11`의 `research/samples/v3/assets/rec1.mp4`로도 복사**해서 쓴다.
2. **견본에 실제 녹화 넣기**: v3 견본의 그려 낸 채팅 화면(S2~S5, `#sApp`)을 rec1.mp4로 바꿔 넣고(HyperFrames `<video class="clip">`, 확대·이동은 GSAP), 다시 렌더 → 블라인드 재채점 → 사용자에게 보고.

## 1. 계정·저장소·기본 규칙

- 인스타 계정 @junglejuggle(정글저글). 운영 저장소 GitHub `monkeywarr12345-star/junglejuggle-ops`(공개 저장소). 규칙은 저장소 루트 `CLAUDE.md`. 사용자에게 보내는 모든 글은 **한국어**.
- 인스타 업로드 자동화는 중지 상태(`pause.json` until 2099). 예약 작업 상당수도 꺼져 있음. 다시 켜는 건 사용자 지시가 있을 때만.
- 유료 결제 금지. 비밀번호·토큰·API 키 입력, 계정 만들기는 Claude가 하지 않고 사용자에게 넘긴다. 삭제는 확인 후에만.
- 다른 계정 둘러보기는 집 Chrome의 개인 계정 @wig_glwiggl로만, 보기만 하고 사람 속도로, 캡차가 나오면 멈춘다. 남의 캡션·댓글 원문과 이미지는 저장하지 않는다. 회사 노트북 브라우저는 쓰지 않는다.
- 틱톡·인스타·유튜브 영상을 스크립트(yt-dlp 등)로 내려받지 않는다.

## 2. 지금 진행 중인 큰 일: "AI 도구 실사용" 계정 전환 검토 (조사만, 적용 전)

- 사용자 지시: "바로 계정에 적용하지 말고, 조사하고 결과를 알려 주면 내가 적용할지 판단한다." → **계정, main 코드, CLAUDE.md, 예약 작업에는 아직 아무것도 적용하지 않음.** 실험은 브랜치 `research/ai-tools-2026-11`에서만. main에는 조사 데이터·예측표만 올림.
- 결과 문서(Claude 문서): "AI 도구 실사용 계정 전환 검토" — https://claude.ai/artifact/2fJWEiod1pwo8FfREqY3P9 (문서 id `0d72306e-df0c-4e94-a2b1-3ad10aa07744`). 사용자는 이 문서에 댓글로 요청하는 경우가 많음.
- 문서 구성: 결론 5줄 → 견본 v3 재작업 → 계정 전환안 → 퀄리티 기준표 → 도구 조사표 → 견본 비교·블라인드 채점 → AI 캐릭터 진행자 검토 → 채택 후보 파이프라인 → 스킬 판정표 → DM 자동화 설계·정책 검토 → 첫 10개 계획안 → **적용 목록(12개, 번호 표)** → 못 본 것과 내가 정할 것.
- 사용자가 적용 목록 번호를 골라 "1, 3, 5번 적용"처럼 말하면 그것만 진행. 추천 순서 5 → 3·4 → 1·2 → 6 → 11 → 7·8 → 10 → 9. (5번 = collect.yml에서 건너뛴 글자 인식(OCR) 도구 설치를 되돌리기.)

## 3. 사용자가 정한 것

- 주제: **AI 도구 실사용**만. 계정은 @junglejuggle만 바꾸고, 기존 게시물 14개(13개 아님, 스킴스 릴스 포함)는 보관 예정(아직 안 함).
- 노출: 화면 녹화·목소리·손은 OK, **얼굴은 싫음**. AI 캐릭터 진행자는 첫 10개 중 2개만 시험하는 안.
- 견본 목소리: **A안 = Supertonic 2, 목소리 F1, 1.25배속**(무료, 코드 MIT, 모델 OpenRAIL-M). 직접 녹음은 필요 없음.
- 배경음: 크레딧 표기 없이 쓰고 싶어 함 → 저장소 자체 제작 음악(`scripts/music.py`, `gen:chill`)으로 바꿈. 음악 없는 판도 같이 만들어 인스타 앱 음악을 붙일 수 있게 함. CC BY 곡은 크레딧이 사용 조건이라 뺄 수 없음.
- 인스타 'AI 정보' 표시: 나중에 켜기로 함.
- HeyGen: 사용자가 무료 가입을 원했으나 Claude는 계정 생성 불가. 게다가 **HeyGen 무료 플랜 결과물은 개인·비상업 용도만 허용**(HeyGen 공식 블로그) → 게시용 견본에는 쓰지 않기로 보류. 사용자가 직접 가입하고 API 키를 GitHub Secrets `HEYGEN_API_KEY`로 넣으면 그때 HyperFrames MCP 커넥터 연결을 돕기로 함.
- 댓글→DM 자동 발송: 지금 권한이 없어 불가(토큰에 댓글·메시지 권한 없음, 고급 접근 심사가 필요할 수 있음, 저장소 공개). 첫 30개는 DM 없이 '프로필 링크에 정리본'.

## 4. 견본 현황

- 벤치마크: 얼굴 나오는 grappt_·adu.aihub와 형식이 다름. **얼굴 없는 기준은 gpt_haterz**(같은 HyperFrames 사용, 고정 캐릭터 플랫 일러스트 + 상단 2줄 제목·노란 밑줄 + 하단 테두리 자막 + UI를 캐릭터가 가리킴 + 내레이션).
- 블라인드 채점(별도 에이전트, 기준표 `research/results/score2/rubric.md`, 7항목 35점):

  | 판 | 기준표 점수 | 벤치마크를 100으로 할 때 |
  |---|---|---|
  | v2 | 60.0% | 약 45 |
  | v3.2 | 62.9% | 약 70 |
  | v3.4 | 62.9% | 약 70 |

  v3.5~3.6(첫 프레임 금액, 겹침 제거, 말투 통일, 선명한 일러스트, 자체 음악)은 아직 채점하지 않음. 남은 가장 큰 차이 = "목업 느낌" → 실제 화면 녹화로 해결 예정.
- 최신 결과물(실험 브랜치): `research/results/v3/v3_A.mp4`(자체 음악), `v3_A_nomusic.mp4`, `contact.jpg`(0.9초 간격 프레임).

## 5. 실험 브랜치 `research/ai-tools-2026-11` 주요 파일

- 견본 v3: `research/samples/v3/`
  - `index.html`: HyperFrames 구성. 장면 s1 훅(img0), sApp(s2~s5: 노트북 img6 확대 → 채팅창, STEP2 큰 입력창 + 생각하는 캐릭터 cut4, STEP3 표 + 가리키는 캐릭터 cut3), s6 결과(img2, -21,000원/월), s7 프롬프트 3개 + 캐릭터(cut3 좌우 반전). 글꼴은 Pretendard 파일을 직접 넣음.
  - `build.py`: 문장별 TTS → 정확한 timeline.js(장면 시각·자막·효과 시점) + 효과음 합성. 목소리 지정 `voice.txt`(예 `supertonic F1 @1.25`). `file` 모드는 `assets/voice/s1.wav…`를 씀.
  - `cutout.py`: 단색 배경 일러스트 배경 지우기. `music.txt`: `gen:chill`(자체 음악).
- 워크플로(모두 실험 브랜치 push로만 실행, 결과를 브랜치에 커밋):
  - `research-v3.yml`: 견본 렌더(목소리마다 v3_<A..>.mp4 + nomusic판 + contact.jpg). 트리거 `research/samples/v3/**`.
  - `research-v3hq.yml`: Z-Image-Turbo(stable-diffusion.cpp, CPU) 일러스트 7장 + Real-ESRGAN 애니 4배 확대 → `research/results/v3tools/imghq/img0~6.jpg`. 장당 15~25분.
  - `research-v3tools.yml`, `research-v3eval.yml`: TTS 4종 비교(Supertonic 2·Qwen3-TTS 0.6B/1.7B·Chatterbox), whisper로 발음 오류율 측정(결과 `research/results/v3tools/eval.json`).
  - 예전 것: `research.yml`, `research-hf2.yml`, `research-bench.yml`, `research-fetch.yml`.
- 기타: `research/dm/dm_bot.py`(보내지 않는 모드), `research/first/01-subscription.md`(1편 대본·촬영 안내), `research/tools/`(저장소 메타, 권한 점검 등).
- main에 올린 것: `playbook/predictions/2026-11-12-ai-tools-first10.md`, `playbook/log/2026-11-12.md`, `data/study/*`.

## 6. 예약 작업

- 팔로워 7일 재측정: trig_01MSCT9yNKZTj4r6WXL77Dns, 2026-11-19 09:10 KST 한 번.

## 7. 알려진 제약

- 클라우드 작업 환경은 GitHub 외 인터넷이 막혀 있음 → 렌더·모델 실행은 GitHub Actions에서. Actions 아티팩트 다운로드는 막혀 있어 결과를 브랜치에 커밋하는 방식.
- Chrome 스크린샷은 최대 약 1568px라 ChatGPT 화면을 캡처하면 글자가 너무 작음(페이지 확대 시 ChatGPT 화면 배치가 깨짐) → 실제 녹화는 OpenScreen이나 휴대폰 화면 녹화로 해야 함.
- Openverse API는 Actions에서 401, FreePD 직접 접속도 실패 → CC0 음악 자동 수급은 막혀 있음.
- Gemini API 무료 등급에는 이미지 생성이 없음(2026.10 기준).
