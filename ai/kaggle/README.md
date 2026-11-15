# Kaggle GPU 도구

`ai/kaggle/` 아래 파일을 main에 push하면 `.github/workflows/kaggle-gpu.yml`이 Kaggle 무료 T4 GPU에서 `kernel.py`를 돌려요. 결과는 `media/ai/kaggle/<run.txt>/`에 커밋돼요.

- 화질 올리기: `media/ai/<id>/ludyte_src/*.mp4` → Real-ESRGAN x2 → 1080×1920 `*_up.mp4`
- 받아쓰기 검사: faster-whisper large-v3로 릴스 내레이션을 대본과 비교 → `whisper_reel.json`
- TTS 비교: Supertonic M1(현재) vs Qwen3-TTS 1.7B(목소리 디자인 / 현재 목소리 복제) vs Chatterbox → `tts_*.mp3`, `status.json`의 줄별 CER
- 필요: 저장소 Secrets `KAGGLE_USERNAME`, `KAGGLE_KEY`(연구 브랜치 실험 때 등록됨). GPU 주간 한도 안에서만 돌아요.
