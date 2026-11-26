import json, wave
w = wave.open('v_fit.wav'); D = round(w.getnframes() / w.getframerate() + 0.15, 2); w.close()
L = lambda t: round(t - 0.05, 3)
# [start, line1, line2, line2_time]
caps = [
    [0, 'AI로 쓴 글,', '사람 눈엔 다 티 나요', 1.36],
    [L(3.21), '근데 그 티를', '26개나 찾아서 지워 주는 스킬이 있어요', 3.93],
    [L(7.27), '이름은', '휴머나이저', 7.84],
    [L(8.86), '위키백과 편집자들이 AI 글 잡아낼 때', '쓰는 기준으로 만든 거고요', 10.9],
    [L(13.2), '깃허브 별이 6만 9천 개인데', '무료예요', 15.36],
    [L(16.13), '설치는 진짜 간단해요', '', None],
    [L(17.85), '깃허브에서 ZIP 받고,', '', None],
    [L(19.49), '클로드에서 스킬로 올리고,', '', None],
    [L(22.2), '글 붙여 넣고', '"휴머나이저로 고쳐 줘" 하면 끝이에요', 23.33],
    [L(25.88), '뜻은 그대로 두고', '말투만 사람처럼 바꿔 줘요', 27.1],
    [L(28.97), '저는 영어 메일 보내기 전에', '꼭 한 번 돌려요', 30.54],
    [L(31.7), '저장해 두고 쓰세요', '', None],
    [L(32.93), "댓글에 '휴먼' 남기면", '설치법이랑 한국어 프롬프트까지', 34.78],
    [L(36.55), '보내 드릴게요', '', None],
]
GH = 'github.com/blader/humanizer'
S = [
    ('hook', 0, 1.36, {'shade': 0.38}),
    ('m_point', 1.36, 3.21, {}),
    ('tells', 3.21, 7.27, {'img': 'src/gh_tells.jpg', 'credit': GH}),
    ('name', 7.27, 8.86, {'img': 'src/gh_header.jpg', 'credit': GH, 'cont': 1}),
    ('wiki', 8.86, 13.2, {'img': 'src/gh_readme.jpg', 'credit': GH, 'cont': 1}),
    ('stars', 13.2, 15.36, {'img': 'src/gh_header.jpg', 'credit': GH + ' · 2026.11.26', 'cont': 1}),
    ('m_wolf', 15.36, 17.1, {}),
    ('step1', 17.1, 19.49, {'img': 'src/gh_code.jpg', 'credit': GH}),
    ('step2', 19.49, 22.2, {'img': 'src/cl_plugins.jpg', 'credit': 'claude.ai 화면 (2026.11.26)', 'cont': 1}),
    ('step3', 22.2, 25.88, {}),
    ('ba', 25.88, 28.97, {'img': 'src/gh_readme.jpg', 'credit': GH + ' README 예시'}),
    ('mail', 28.97, 30.54, {'img': 'src/gh_readme.jpg', 'credit': GH + ' README 예시', 'cont': 1}),
    ('m_cool', 30.54, 31.95, {}),
    ('cta', 31.95, D, {}),
]
scenes = []
for sid, a, b, o in S:
    d = {'id': sid, 't0': a, 't1': b}; d.update(o); scenes.append(d)
ev = {'s1': 17.85, 's2': 19.49, 's3': 22.2, 'say': 22.88, 'done': 24.82, 'type': 33.0, 'dm': 34.78}
json.dump({'dur': D, 'caps': caps, 'scenes': scenes, 'ev': ev, 'pops': [0.55, 4.2, 13.8, 18.0, 20.1, 24.82, 35.0]}, open('ov/tl.json', 'w'), ensure_ascii=False, indent=1)
print('dur', D)
