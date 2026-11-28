const $ = (s) => document.querySelector(s);
const cl = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const seg = (t, a, b) => cl((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const eo = (k) => 1 - Math.pow(1 - k, 3);
const bo = (k, s = 1.9) => { k = cl(k); const c3 = s + 1; return 1 + c3 * Math.pow(k - 1, 3) + s * Math.pow(k - 1, 2); };
const css = (e, o) => { for (const k in o) e.style[k] = o[k]; };
const pop = (e, t, a, base = '', d = 0.38) => { const k = bo(seg(t, a, a + d)); css(e, { opacity: t >= a ? 1 : 0, transform: `${base} scale(${k})` }); };
const wob = (t, f = 1.3, a = 1.5) => Math.sin(t * f * 6.283) * a;

// 녹음(ElevenLabs 11/28 21:20, 쉼 0.28 압축 + 1.1배) 실측 시작점 + 앞 5초 반전 훅(대사 없음)
const CAPS = [
 [0, ''],
 [5.0, '이렇게 <b>바통</b> 넘기듯이 쓰면요,'], [6.93, 'AI도 결과가 <b>확</b> 달라지거든요'],
 [9.14, '<b>클로드</b>랑 <b>챗GPT</b>,'], [10.67, '<b>제미나이</b>를 한 팀으로 묶는 건데요'],
 [12.8, '먼저 자료 조사는 <b>제미나이</b>한테 시키면 돼요'], [15.46, '<b>딥 리서치</b>가 출처까지'], [17.32, '달아서 쫙 정리해 주거든요'],
 [18.68, '그걸 그대로 <b>클로드</b>한테 넘겨 주면요,'], [20.92, '흐름 잡아서 깔끔한 <b>글</b>로 써 줘요'],
 [23.02, '마지막으로 <b>챗GPT</b>한테 넘기고요,'], [25.2, '빠진 거 없나 <b>검토</b>도 하고,'], [26.84, '들어갈 <b>이미지</b>까지 만들어 줘요'],
 [28.49, '여기서 <b>중요한 게</b> 하나 있는데요,'], [30.29, '앞에서 나온 결과를'], [31.52, '<b>통째로 복사</b>해서 넘겨야 돼요'],
 [33.41, '셋 다 <b>무료</b>로 시작할 수 있어요'], [35.29, '<b>한도</b>가 좀 있긴 한데요'],
 [36.75, '따라 해 보시게 <b>저장</b>해 두시고요,'], [38.47, '팔로우하고 댓글에'], [39.93, "<b>'한팀'</b>이라고 남겨 주시면"], [41.73, '단계별 <b>프롬프트</b> 보내 드릴게요'],
];
const SW = 5.0;
const SC = [['intro', 0], ['hook', SW], ['r1', 12.8], ['r2', 18.68], ['r3', 23.02], ['key', 28.49], ['free', 33.41], ['save', 36.75], ['cta', 38.47]];
const DUR = 44.5;
const TR = location.href.includes('tr');
if (TR) document.documentElement.classList.add('tr');
if (location.href.includes('still') || location.href.includes('cover')) document.documentElement.classList.add('still');
const HOLE = "path(evenodd, 'M0 0H1080V1920H0Z M230 630H850V1250H230Z')";
const CLIPSC = { hook: 1, key: 1, free: 1, save: 1 };
function wipe(sel, t, a) { const w = $(sel + ' .wipe'); if (!w) return; w.style.transform = a < 0 ? 'translateY(-101%)' : `translateY(${-eo(seg(t, a, a + 0.38)) * 101}%)`; }
const DOO = [['star', 70, 1590, '#111111'], ['spark', 930, 1600, '#FFFFFF'], ['squig', 900, 470, '#111111'], ['circ', 60, 540, '#FFFFFF'], ['spark', 980, 1250, '#111111'], ['star', 40, 1300, '#FFFFFF']];
const shp = { star: 'M45,5 L56,33 L86,34 L62,53 L71,83 L45,66 L19,83 L28,53 L4,34 L34,33 Z', spark: 'M45,5 Q50,40 85,45 Q50,50 45,85 Q40,50 5,45 Q40,40 45,5 Z', squig: 'M5,45 Q20,15 35,45 T65,45 T95,45', circ: 'M45,10 A35,35 0 1 1 44.9,10 Z' };
$('#doos').innerHTML = DOO.map(([k, x, y, c], i) => `<svg class="doo" id="d${i}" viewBox="0 0 90 90" style="left:${x}px;top:${y}px"><path d="${shp[k]}" fill="${k === 'squig' ? 'none' : c}" stroke="${k === 'squig' ? c : '#141414'}" stroke-width="${k === 'squig' ? 9 : 5}" stroke-linejoin="round" stroke-linecap="round"/></svg>`).join('');

function winIn(e, t, a = 0) { const k = bo(seg(t, a, a + 0.45), 1.5); css(e, { opacity: t >= a ? 1 : 0, transform: `translateY(${(1 - eo(seg(t, a, a + 0.35))) * 140}px) rotate(${lerp(-4, -1, k) + wob(t, 0.25, 0.4)}deg) scale(${lerp(0.7, 1, k)})` }); }
function head(S, t) { const k = $(`#${S} .kick`), ti = $(`#${S} .title`); if (k) pop(k, t, 0.0, '', 0.3); if (ti) pop(ti, t, 0.05, '', 0.42); }
const nm = (e, t, a) => pop(e, t, a, `translateX(-50%) rotate(${wob(t + a, 0.5, 2)}deg)`);
const chipC = (e, t, a) => pop(e, t, a, 'translateX(-50%)');
const Q1 = 'AI 한 팀 활용법, 자료 조사해 줘';
const U = {
 intro(t) {},
 hook(t, T) {
  pop($('#hA'), t, -1, '', 0.3); pop($('#hB'), t, -1, `rotate(${-1.5 + wob(t, 0.5, 0.5)}deg)`, 0.42);
  wipe('#ccA', t, 0.0);
  nm($('#nC'), T, 9.14); nm($('#nG'), T, 9.75); nm($('#nM'), T, 10.67);
 },
 r1(t, T) { head('r1', t); winIn($('#w1'), t, 0.05); const n = Math.floor(cl((t - 0.35) / 1.0) * Q1.length); $('#q1').textContent = Q1.slice(0, n) + (n < Q1.length ? '|' : '');
  pop($('#rh'), T, 15.0, '', 0.3); [['#ra', 15.5], ['#rb', 15.9], ['#rc', 16.3]].forEach(([q, a]) => css($(q), { opacity: T >= a ? 1 : 0 }));
  [['#s1', 16.0], ['#s2', 16.4], ['#s3', 16.8]].forEach(([q, a]) => pop($(q), T, a, '', 0.3)); chipC($('#c1'), T, 17.32); },
 r2(t, T) { head('r2', t); winIn($('#w2'), t, 0.05); const k = bo(seg(t, 0.5, 0.85), 2); css($('#paste'), { opacity: t >= 0.5 ? 1 : 0, transform: `scale(${k})` });
  for (let i = 0; i < 5; i++) { const a = 20.92 + i * 0.28; const e = $('#L' + i); css(e, { transformOrigin: '0 50%', transform: `scaleX(${eo(seg(T, a, a + 0.3))})`, background: T >= a + 0.3 ? '#111' : '#E6E6E6' }); }
  chipC($('#c2'), T, 21.9); },
 r3(t, T) { head('r3', t); winIn($('#w3'), t, 0.05); [0, 1, 2].forEach((i) => { const a = 25.2 + i * 0.4; const on = T >= a; const b = $('#kb' + i); b.textContent = on ? '✓' : ''; css(b, { background: on ? 'var(--ink)' : '#fff', color: '#fff', transform: `scale(${on ? bo(seg(T, a, a + 0.25)) : 1})` }); });
  pop($('#pic'), T, 26.84, `rotate(${wob(t, 0.4, 1.5)}deg)`, 0.45); chipC($('#c3'), T, 27.4); },
 key(t, T) { head('key', t); wipe('#ccB', t, 0.02); pop($('#kc1'), T, 30.29, '', 0.3); css($('#arr'), { opacity: T >= 31.0 ? 1 : 0 }); pop($('#kc2'), T, 31.52, '', 0.3);
  const p1 = T > 30.7 && T < 30.95, p2 = T > 31.9 && T < 32.15; css($('#kc1'), { boxShadow: p1 ? '0 2px 0 var(--ink)' : '0 10px 0 var(--ink)' }); css($('#kc2'), { boxShadow: p2 ? '0 2px 0 var(--ink)' : '0 10px 0 var(--ink)' }); },
 free(t, T) { head('free', t); wipe('#ccC', t, 0.02); [0, 1, 2].forEach((i) => nm($('#f' + i), t, 0.5 + i * 0.25)); const k = seg(T, 35.29, 35.5); css($('#lim'), { opacity: T >= 35.29 ? 1 : 0, transform: `rotate(8deg) scale(${lerp(2.4, 1, eo(k))})` }); },
 save(t) { head('save', t); const k = bo(seg(t, 0.25, 0.65), 2.2); css($('#bm'), { opacity: t >= 0.25 ? 1 : 0, transform: `scale(${k}, ${lerp(0.6, 1, k)}) rotate(${12 + wob(t, 1.2, 4)}deg)` }); },
 cta(t) { head('cta', t); const f = t > 0.5; const fe = $('#fol'); fe.textContent = f ? '팔로잉 ✓' : '팔로우'; css(fe, { opacity: 1, background: f ? '#fff' : 'var(--ink)', color: f ? 'var(--ink)' : '#fff', transform: `translateX(-50%) scale(${f ? bo(seg(t, 0.5, 0.75)) : 1})` }); winIn($('#cbox'), t, 0.8); $('#typed').textContent = t > 1.75 ? '한팀' : (t > 1.55 ? '한' : ''); $('#caret2').style.opacity = Math.floor(t * 4) % 2 ? 0.2 : 1; const b = eo(seg(t, 3.3, 3.75)); css($('#dm'), { opacity: b > 0 ? 1 : 0, transform: `translateX(${(1 - b) * 900}px) rotate(${lerp(8, 1.5, b)}deg)` }); },
};

function render(t) {
 let i = 0; for (let k = 0; k < SC.length; k++) if (t >= SC[k][1]) i = k;
 const [id, t0] = SC[i];
 document.querySelectorAll('.S').forEach((e) => (e.style.display = e.id === id ? 'block' : 'none'));
 U[id](t - t0, t);
 const IN = id === 'intro'; ['#logo', '#cap', '#doos', '#bg'].forEach((q) => ($(q).style.visibility = IN ? 'hidden' : 'visible'));
 $('#bg').style.clipPath = (TR && CLIPSC[id]) ? HOLE : 'none';
 const fl = t < SW ? eo(seg(t, SW - 0.16, SW)) : 1 - eo(seg(t, SW, SW + 0.3)); $('#flash').style.opacity = fl;
 const lb = t - t0; const bk = seg(lb, 0, 0.35); css($('#burst'), { opacity: i > 1 && bk < 1 ? (1 - bk) * 0.28 : 0, transform: `scale(${1 + eo(bk) * 34})` });
 let c = 0; for (let k = 0; k < CAPS.length; k++) if (t >= CAPS[k][0]) c = k;
 const ce = $('#capIn'); if (ce.dataset.k != c) { ce.innerHTML = CAPS[c][1]; ce.dataset.k = c; }
 $('#cap').style.visibility = IN || !CAPS[c][1] ? 'hidden' : 'visible';
 const ck = bo(seg(t, CAPS[c][0], CAPS[c][0] + 0.22), 1.6); ce.style.transform = `scale(${lerp(0.85, 1, ck)}) rotate(${c % 2 ? 0.8 : -0.8}deg)`;
 const pg = ['r1', 'r2', 'r3'].indexOf(id); $('#prog').style.display = pg >= 0 ? 'flex' : 'none'; document.querySelectorAll('.pd').forEach((e, k) => e.classList.toggle('on', k === pg));
 DOO.forEach((d, k) => css($('#d' + k), { transform: `translateY(${Math.sin(t * 1.3 + k) * 12}px) rotate(${Math.sin(t * 0.9 + k * 2) * 14}deg)` }));
}
window.__scenes = SC; window.__dur = DUR;
window.__timelines = { main: { seek: async (t) => { render(t); }, duration: () => DUR } };
if (location.href.includes('cover')) { window.__cover = () => { render(12.0); $('#cap').style.display = 'none'; $('#flash').style.display = 'none'; $('#hA').textContent = '클로드·챗GPT·제미나이'; css($('#hA'), { top: '250px', fontSize: '50px', color: '#333' }); $('#hB').innerHTML = 'AI 셋을<br><v>한 팀</v>으로 쓰는 법'; css($('#hB'), { top: '318px', fontSize: '100px', transform: 'rotate(-1.5deg)' }); css($('#ccA'), { top: '600px' }); ['#nC', '#nG', '#nM'].forEach((q) => css($(q), { top: '1150px' }));
 $('#hook').insertAdjacentHTML('beforeend', '<div class="card" style="left:70px;top:1300px;width:940px;padding:22px 26px;background:#fff;transform:rotate(-1deg);display:flex;align-items:center;justify-content:center;gap:14px;font-size:40px;font-weight:900;white-space:nowrap">조사 <span style="font-size:44px">→</span> 초안 <span style="font-size:44px">→</span> 검토·이미지</div><div class="chip vi" style="left:620px;top:1440px;font-size:38px;transform:rotate(4deg)">단계별 프롬프트 3개</div><div class="ex" style="left:0;right:0;top:1560px;text-align:center;font-size:30px">셋 다 무료로 시작 · 한도 있어요</div>'); }; }
document.fonts.ready.then(() => { if (window.__cover) window.__cover(); else render(0); window.__ready = true; });
