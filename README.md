# junglejuggle-ops

Instagram @junglejuggle 자동 게시용 저장소예요. GitHub Actions가 30분마다 `queue/`를 확인해서, 게시 시각이 지난 항목을 인스타그램에 올려요.

## 게시물 예약하기

1. 이미지나 영상을 `media/`에 올려요.
2. `queue/`에 JSON 파일을 하나 만들어요. 파일 이름 순서대로 처리돼요.

```json
{
  "type": "feed",
  "image": "media/2026-11-09-morning.jpg",
  "caption": "캡션 내용 #해시태그",
  "publish_at": "2026-11-09T09:00:00+09:00"
}
```

| 필드 | 설명 |
|---|---|
| `type` | `feed`(기본값), `story`, `reel`, `carousel` |
| `image` / `video` | 저장소 안 경로 또는 https 주소 |
| `items` | carousel 전용. `[{"image": "..."}, {"video": "..."}]` 형식으로 2~10개 |
| `caption` | 캡션. 스토리에서는 무시돼요 |
| `publish_at` | 게시 시각. 시간대를 꼭 붙여요(`+09:00`). 비워 두면 다음 실행 때 바로 올라가요 |

`queue/`가 바뀌어 main에 푸시되면 곧바로 한 번 실행되고, 그 뒤로는 30분마다 확인해요.

## 결과 확인

- 게시가 끝난 항목은 `posted/`로 옮겨지고, 미디어 ID가 함께 기록돼요.
- 실패한 항목은 `failed/`로 옮겨지고, 오류 메시지가 함께 기록돼요. 고친 뒤 다시 `queue/`에 넣으면 돼요.
- Actions 탭에서 **Publish to Instagram** → **Run workflow**를 누르면 바로 실행할 수 있어요. `dry_run`을 켜면 실제로 올리지 않고 목록만 보여줘요.

## 미디어 규칙(Instagram API 기준)

- 피드 이미지는 JPEG만 돼요. 비율은 4:5~1.91:1 사이여야 해요.
- 스토리는 9:16(1080×1920)을 권장해요.
- 릴스는 MP4(H.264)이고 9:16을 권장해요.
- 계정당 24시간에 게시할 수 있는 수에 제한이 있어요.

## 토큰 관리

게시는 두 가지 로그인 방식을 쓸 수 있어요. `IG_LOGIN_TOKEN`이 있으면 그걸 먼저 쓰고, 그 로그인이 거부되면 예전 방식으로 한 번 더 시도해요(`scripts/ig_api.py`).

### 1. 인스타그램 로그인 방식 (권장, 페이스북 없이 게시)

- Instagram API with Instagram Login(`graph.instagram.com`)이에요. 페이스북 페이지 연결이 필요 없고, 페이스북 계정에 보안 확인이 걸려도 게시가 멈추지 않아요.
- 처음 한 번 설정: Meta 개발자 앱 대시보드 → **Instagram → API setup with Instagram business login** → 정글저글 계정 옆 **Generate token** → 인스타그램으로 로그인 → 나온 토큰을 Secrets의 `IG_LOGIN_TOKEN`에 넣어 주세요. 권한은 `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_insights`가 필요해요.
- `IG_LOGIN_USER_ID`는 비워 둬도 돼요(`/me`로 자동으로 찾음).
- 토큰은 60일짜리예요. **Check Instagram token** 워크플로가 매주 월요일에 토큰을 갱신해요. 갱신 결과로 새 토큰이 나오면 `GH_SECRETS_TOKEN`(이 저장소에 "Secrets: Read and write" 권한을 준 GitHub fine-grained 토큰)이 있을 때 `IG_LOGIN_TOKEN`을 자동으로 바꿔 줘요. 없으면 60일 안에 대시보드에서 토큰을 다시 만들어 넣어 주세요.
- 이 방식은 다른 계정 조회(business_discovery)를 지원하지 않아요. 그래서 경쟁 계정 벤치마크 수집은 아래 페이스북 방식 토큰이 있어야 돌아가고, 없으면 건너뛰어요.

### 2. 페이스북 로그인 방식 (예전 방식, 벤치마크 수집용)

- Secrets의 `IG_ACCESS_TOKEN`(60일 장기 토큰)과 `IG_USER_ID`를 써요. 인스타그램 로그인 토큰이 없거나 거부될 때 게시에도 쓰여요.
- 만료가 10일 안으로 다가오면 **Check Instagram token** 실행이 실패로 표시되고 GitHub가 메일을 보내요.
- 갱신하려면 그래프 API 탐색기에서 같은 권한으로 토큰을 새로 만들고, 액세스 토큰 디버거에서 연장한 뒤 `IG_ACCESS_TOKEN` 값을 바꿔 주세요.
