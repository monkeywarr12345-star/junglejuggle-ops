const $ = (s) => document.querySelector(s);
const cl = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const seg = (t, a, b) => cl((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const eo = (k) => 1 - Math.pow(1 - k, 3);
const bo = (k, s = 1.9) => { k = cl(k); const c3 = s + 1; return 1 + c3 * Math.pow(k - 1, 3) + s * Math.pow(k - 1, 2); };
const css = (e, o) => { for (const k in o) e.style[k] = o[k]; };
const pop = (e, t, a, base = '', d = 0.38) => { const k = bo(seg(t, a, a + d)); css(e, { opacity: t >= a ? 1 : 0, transform: `${base} scale(${k})` }); };
const wob = (t, f = 1.3, a = 1.5) => Math.sin(t * f * 6.283) * a;

// 시안 타이밍(녹음 전 추정: 글자 수 ÷ 6.2 + 쉼 0.15초). 녹음이 오면 무음 구간 측정값으로 교체.
const LINES = [
 ['아침마다 메일함 여는 거,', 'hook'], ['<b>오늘로</b> 끝내세요', 'hook'],
 ['클로드가 평일 <b>아침 7시</b>에', 'clock'], ['먼저 <b>브리핑</b>해 줘요', 'clock'],
 ['오늘 일정, 답장할 메일,', 'brief'], ['<b>할 일</b>까지 한 번에요', 'brief'],
 ['노트북 덮어 놔도', 'laptop'], ['<b>알아서</b> 돌아가요', 'laptop'],
 ['세팅은 <b>세 단계</b>예요', 'steps'],
 ['<b>메일</b>이랑 <b>캘린더</b> 연결하고,', 's1'],
 ['예약 작업에 <b>브리핑 프롬프트</b> 넣고,', 's2'],
 ['<b>평일 아침 7시</b>로 고르면 끝', 's3'],
 ['내일 아침이면 <b>브리핑</b>이 정리돼 있어요', 'morning'],
 ['<b>Pro 요금제</b>부터 돼요', 'plan'],
 ['세팅할 때 다시 보게', 'save'], ['<b>저장</b>해 두세요', 'save'],
 ["팔로우하고 댓글에 <b>'비서'</b>", 'cta'], ['남기면 <b>프롬프트</b> 보내 드려요', 'cta'],
];
const CAPS = []; const SC = []; let T = 0;
for (const [h, s] of LINES) { CAPS.push([T, h]); if (!SC.length || SC[SC.length - 1][0] !== s) SC.push([s, T]); T += h.replace(/<[^>]+>/g, '').replace(/[ ,'.]/g, '').length / 6.2 + 0.18; }
const DUR = T + 0.9;
const st = (s) => SC.find((x) => x[0] === s)[1];

const DOO = [['star', 70, 1590, '#111111'], ['spark', 930, 1600, '#FFFFFF'], ['squig', 900, 470, '#111111'], ['circ', 60, 540, '#FFFFFF'], ['spark', 980, 1250, '#111111'], ['star', 40, 1300, '#FFFFFF']];
const shp = { star: 'M45,5 L56,33 L86,34 L62,53 L71,83 L45,66 L19,83 L28,53 L4,34 L34,33 Z', spark: 'M45,5 Q50,40 85,45 Q50,50 45,85 Q40,50 5,45 Q40,40 45,5 Z', squig: 'M5,45 Q20,15 35,45 T65,45 T95,45', circ: 'M45,10 A35,35 0 1 1 44.9,10 Z' };
$('#doos').innerHTML = DOO.map(([k, x, y, c], i) => `<svg class="doo" id="d${i}" viewBox="0 0 90 90" style="left:${x}px;top:${y}px"><path d="${shp[k]}" fill="${k === 'squig' ? 'none' : c}" stroke="${k === 'squig' ? c : '#141414'}" stroke-width="${k === 'squig' ? 9 : 5}" stroke-linejoin="round" stroke-linecap="round"/></svg>`).join('');
$('#ticks').innerHTML = [...Array(12)].map((_, i) => { const a = i * Math.PI / 6; return `<line x1="${280 + Math.sin(a) * 200}" y1="${290 - Math.cos(a) * 200}" x2="${280 + Math.sin(a) * 220}" y2="${290 - Math.cos(a) * 220}" stroke="#111" stroke-width="${i % 3 ? 6 : 12}" stroke-linecap="round"/>`; }).join('');
$('#rays').innerHTML = [...Array(10)].map((_, i) => { const a = i * Math.PI / 5; return `<line x1="${150 + Math.sin(a) * 95}" y1="${150 - Math.cos(a) * 95}" x2="${150 + Math.sin(a) * 135}" y2="${150 - Math.cos(a) * 135}" stroke="#111" stroke-width="12" stroke-linecap="round"/>`; }).join('');

function winIn(e, t, a = 0) { const k = bo(seg(t, a, a + 0.45), 1.5); css(e, { opacity: t >= a ? 1 : 0, transform: `translateY(${(1 - eo(seg(t, a, a + 0.35))) * 140}px) rotate(${lerp(-4, -1, k) + wob(t, 0.25, 0.4)}deg) scale(${lerp(0.7, 1, k)})` }); }
function head(S, t) { const k = $(`#${S} .kick`), ti = $(`#${S} .title`); if (k) pop(k, t, 0.0, '', 0.3); if (ti) pop(ti, t, 0.05, '', 0.42); }
function chipC(e, t, a) { pop(e, t, a, 'translateX(-50%)'); }
const hand = (e, deg) => e.setAttribute('transform', `rotate(${deg} 280 290)`);
const INST = '매일 아침 내 메일과 캘린더를 보고 브리핑해 줘.\n① 오늘 일정과 준비할 것\n② 오늘 답장해야 할 메일\n③ 할 일 우선순위 …';

const U = {
 hook(t) {
  // 0초 프레임부터 제목·화면이 다 보이게(벤치마크 규칙 ①)
  css($('#hA'), { opacity: 1, transform: `scale(${1 + 0.02 * Math.sin(t * 3)})` }); css($('#hB'), { opacity: 1, transform: `rotate(${-1.5 + wob(t, 0.5, 0.5)}deg) scale(${1 + 0.03 * Math.sin(t * 2.4)})` });
  css($('#hWin'), { opacity: 1, transform: `translateY(${-t * 12}px) rotate(${-1 + wob(t, 0.25, 0.4)}deg)` }); css($('#hChip'), { opacity: 1, transform: `rotate(-6deg) translateY(${Math.sin(t * 4) * 6}px)` });
  const k = seg(t, 1.55, 1.75); css($('#hStamp'), { opacity: t >= 1.55 ? 1 : 0, transform: `rotate(-12deg) scale(${lerp(2.4, 1, eo(k))})` });
 },
 clock(t) { head('clock', t); pop($('#clk'), t, 0.05, `rotate(${wob(t, 3, t < 1.2 ? 2.5 : 0.4)}deg)`, 0.45); const k = eo(seg(t, 0.2, 1.2)); hand($('#mh'), lerp(-300, 0, k) ); hand($('#hh'), lerp(150, 210, k)); chipC($('#cChip'), t, 1.4); },
 brief(t) { head('brief', t); winIn($('#bCard'), t, 0.05); [0, 1, 2].forEach((i) => pop($('#g' + i), t, 0.45 + i * 0.5, '', 0.35)); },
 laptop(t) { head('laptop', t); const k = eo(seg(t, 0.2, 0.8)); $('#lid').style.transform = `scaleY(${lerp(1, 0.08, k)})`; css($('#zz'), { opacity: t > 0.9 ? 1 : 0, transform: `translateY(${-Math.max(0, t - 0.9) * 30}px)` }); chipC($('#lChip'), t, 1.1); },
 steps(t) { head('steps', t); [['#n1', '#l1', 0.25], ['#n2', '#l2', 0.55], ['#n3', '#l3', 0.85]].forEach(([n, l, a]) => { pop($(n), t, a, `rotate(${wob(t + a, 0.5, 4)}deg)`, 0.4); pop($(l), t, a + 0.08); }); },
 s1(t) { head('s1', t); pop($('#t1'), t, 0.05, `rotate(-2deg)`); pop($('#t2'), t, 0.2, `rotate(2deg)`);
  const p = [[300, 860, 0.3, 0.7], [790, 860, 1.0, 1.4]]; let x = 950, y = 1300;
  p.forEach(([tx, ty, a, b], i) => { if (t >= a) { const m = eo(seg(t, a, b)); x = lerp(i ? 300 : 950, tx, m); y = lerp(i ? 860 : 1300, ty, m); } const on = t > b + 0.05; const s = $('#st' + (i + 1)); s.textContent = on ? '연결됨 ✓' : '연결'; css(s, { background: on ? 'var(--ink)' : '#fff', color: on ? '#fff' : 'var(--ink)' }); });
  css($('#cur'), { left: x + 'px', top: y + 'px' }); const r = t < 1.0 ? seg(t, 0.72, 1.0) : seg(t, 1.42, 1.7); css($('#ring'), { left: x - 20 + 'px', top: y - 20 + 'px', opacity: r > 0 && r < 1 ? 1 - r : 0, transform: `scale(${1 + r * 3})` }); },
 s2(t) { head('s2', t); winIn($('#bWin'), t, 0); const n = Math.floor(cl((t - 0.3) / 1.5) * INST.length); $('#inst').innerHTML = INST.slice(0, n).replace(/\n/g, '<br>'); chipC($('#bChip'), t, 1.2); },
 s3(t) { head('s3', t); winIn($('#cWin'), t, 0); const on = t > 0.6; css($('#wk'), { background: on ? 'var(--ink)' : '#fff', color: on ? '#fff' : 'var(--ink)', borderRadius: '14px' }); $('#wkc').textContent = on ? '✓' : ''; css($('#wkc'), { borderColor: on ? '#fff' : 'var(--ink)' });
  $('#tm').textContent = t > 1.0 ? '07:00 AM' : '--:--'; css($('#saveBtn'), { transform: `scale(${t > 1.3 ? bo(seg(t, 1.3, 1.5)) : 1})` });
  const k = seg(t, 1.5, 1.7); css($('#done'), { opacity: t >= 1.5 ? 1 : 0, transform: `rotate(-10deg) scale(${lerp(2.4, 1, eo(k))})` }); },
 morning(t) { head('morning', t); pop($('#sun'), t, 0.05, `rotate(${t * 20}deg)`, 0.5); const b = eo(seg(t, 0.4, 0.8)); css($('#noti'), { opacity: b > 0 ? 1 : 0, transform: `translateY(${(1 - b) * -500}px) rotate(${lerp(-6, -1, b)}deg)` }); },
 plan(t) { head('plan', t); winIn($('#pCard'), t, 0.05); [0, 1, 2, 4, 3].forEach((i, j) => css($('#p' + i), { opacity: t > 0.3 + j * 0.12 ? 1 : 0 })); },
 save(t) { head('save', t); const k = bo(seg(t, 0.1, 0.5), 2.2); css($('#bm'), { opacity: t >= 0.1 ? 1 : 0, transform: `scale(${k}, ${lerp(0.6, 1, k)}) rotate(${wob(t, 1.2, 4)}deg)` }); },
 cta(t) { head('cta', t); const f = t > 0.5; const fe = $('#fol'); fe.textContent = f ? '팔로잉 ✓' : '팔로우'; css(fe, { opacity: 1, background: f ? '#fff' : 'var(--ink)', color: f ? 'var(--ink)' : '#fff', transform: `translateX(-50%) scale(${f ? bo(seg(t, 0.5, 0.75)) : 1})` }); winIn($('#cbox'), t, 0.8); $('#typed').textContent = t > 1.3 ? '비서' : (t > 1.1 ? '비' : ''); $('#caret2').style.opacity = Math.floor(t * 4) % 2 ? 0.2 : 1; const b = eo(seg(t, 2.0, 2.45)); css($('#dm'), { opacity: b > 0 ? 1 : 0, transform: `translateX(${(1 - b) * 900}px) rotate(${lerp(8, 1.5, b)}deg)` }); },
};

function render(t) {
 let i = 0; for (let k = 0; k < SC.length; k++) if (t >= SC[k][1]) i = k;
 const [id, t0] = SC[i];
 document.querySelectorAll('.S').forEach((e) => (e.style.display = e.id === id ? 'block' : 'none'));
 U[id](t - t0, t);
 const lb = t - t0; const bk = seg(lb, 0, 0.35); css($('#burst'), { opacity: i > 0 && bk < 1 ? (1 - bk) * 0.28 : 0, transform: `scale(${1 + eo(bk) * 34})` });
 let c = 0; for (let k = 0; k < CAPS.length; k++) if (t >= CAPS[k][0]) c = k;
 const ce = $('#capIn'); if (ce.dataset.k != c) { ce.innerHTML = CAPS[c][1]; ce.dataset.k = c; }
 const ck = bo(seg(t, CAPS[c][0], CAPS[c][0] + 0.22), 1.6); ce.style.transform = `scale(${lerp(0.85, 1, ck)}) rotate(${c % 2 ? 0.8 : -0.8}deg)`;
 const pg = ['s1', 's2', 's3'].indexOf(id); $('#prog').style.display = pg >= 0 ? 'flex' : 'none'; document.querySelectorAll('.pd').forEach((e, k) => e.classList.toggle('on', k === pg));
 DOO.forEach((d, k) => css($('#d' + k), { transform: `translateY(${Math.sin(t * 1.3 + k) * 12}px) rotate(${Math.sin(t * 0.9 + k * 2) * 14}deg)` }));
}
window.__scenes = SC; window.__dur = DUR;
window.__timelines = { main: { seek: async (t) => { render(t); }, duration: () => DUR } };
if (location.href.includes('cover')) { const Y = 130; $('#cap').style.display = 'none'; $('#logo').style.top = 112 + Y + 'px'; $('#hA').textContent = '클로드 예약 작업 하나로'; css($('#hA'), { fontSize: '50px', color: '#55524c', top: 250 + Y + 'px' }); $('#hB').innerHTML = '아침 메일함<br><v>오늘로 끝</v>'; css($('#hB'), { fontSize: '108px', top: 330 + Y + 'px' }); $('#hWin').style.top = 700 + Y + 'px'; $('#hStamp').style.top = 1150 + Y + 'px'; $('#hStamp').textContent = '평일 7시'; $('#hChip').style.top = 1300 + Y + 'px'; $('#hChip').textContent = '세팅 3단계'; document.querySelectorAll('.doo').forEach((e) => (e.style.marginTop = Y + 'px')); }
document.fonts.ready.then(() => { render(0); window.__ready = true; });
