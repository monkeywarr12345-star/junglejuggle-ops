# 11/28 러다이트 사용 기록
- 캐릭터 이미지: image request 639bb450 → 노란 연필을 흑백으로 고친 reference_edit 5f8d1e2a → asset e69a63f0 (judges_lineup.png, 모든 클립 first_frame)
- 클립(1:1, 5초, native_high + 1080p 업스케일, 무음): A 도장 쾅(run 22f12cd6) · B 한 명씩 인사(ef5ea681) · C 점수판(96a18fb8) · D 엄지척(af612b73)
- 합성: 굵은 테두리 카드(내부 888x520 @96,636)에 클립을 흑백·흰색 보정(hue s=0, curves)해서 깔고, HTML 오버레이는 투명 프레임(?tr, #bg에 구멍)으로 위에 얹음. 글자·점수(7·6·5·4)·명패·도장은 전부 우리 그래픽.
- 색: 전 과정 RGB로 합성 후 마지막에 BT.709 tv로 한 번만 변환 → 배경 255,255,255 확인
