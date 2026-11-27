const $ = (s) => document.querySelector(s);
const cl = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const seg = (t, a, b) => cl((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const eo = (k) => 1 - Math.pow(1 - k, 3);
const bo = (k, s = 1.9) => { k = cl(k); const c3 = s + 1; return 1 + c3 * Math.pow(k - 1, 3) + s * Math.pow(k - 1, 2); };
const css = (e, o) => { for (const k in o) e.style[k] = o[k]; };
const pop = (e, t, a, base = '', d = 0.38) => { const k = bo(seg(t, a, a + d)); css(e, { opacity: t >= a ? 1 : 0, transform: `${base} scale(${k})` }); };
const wob = (t, f = 1.3, a = 1.5) => Math.sin(t * f * 6.283) * a;

// 시안 타이밍(녹음 전 추정치). 녹음이 오면 무음 구간 측정값으로 교체.
const CAPS = [
 [0.00, '이력서 내기 전에,'], [1.25, '심사위원 <b>다섯 명</b>한테'], [2.40, '<b>먼저 떨어져</b> 보세요'],
 [3.70, '클로드 프로젝트에'], [4.80, '<b>심사위원단</b>을 앉혀 두는 거예요'],
 [6.70, '인사·팀장·임원·채용 시스템·맞춤법까지'], [9.20, '각자 <b>점수</b> 매기고'], [10.40, '<b>떨어뜨릴 이유</b>부터 말해 줘요'],
 [12.20, '<b>무료 플랜</b>도 되고,'], [13.30, '세팅은 <b>세 단계</b>예요'],
 [14.60, '<b>프로젝트</b> 만들고,'], [15.80, '지침에 <b>심사위원 프롬프트</b> 붙여 넣고,'], [17.90, '이력서랑 <b>채용 공고</b> 올리면 끝'],
 [19.90, '그다음부턴 <b>"심사해 줘"</b> 한마디'],
 [22.00, '<b>전화번호·주소</b>는 지우고 올리세요'],
 [24.00, '지원할 때마다 꺼내 쓰게'], [25.20, '<b>저장</b>해 두세요'],
 [26.40, "팔로우하고 <b>'심사'</b> 남기면"], [27.80, '<b>프롬프트 전체</b> 보내 드릴게요'],
];
const SC = [['hook', 0], ['proj', 3.7], ['panel', 6.7], ['score', 9.2], ['steps', 12.2], ['s1', 14.6], ['s2', 15.8], ['s3', 17.9], ['ask', 19.9], ['priv', 22.0], ['save', 24.0], ['cta', 26.4]];
const DUR = 30.6;

const DOO = [['star', 70, 1590, '#111111'], ['spark', 930, 1600, '#FFFFFF'], ['squig', 900, 470, '#111111'], ['circ', 60, 540, '#FFFFFF'], ['spark', 980, 1250, '#111111'], ['star', 40, 1300, '#FFFFFF']];
const shp = { star: 'M45,5 L56,33 L86,34 L62,53 L71,83 L45,66 L19,83 L28,53 L4,34 L34,33 Z', spark: 'M45,5 Q50,40 85,45 Q50,50 45,85 Q40,50 5,45 Q40,40 45,5 Z', squig: 'M5,45 Q20,15 35,45 T65,45 T95,45', circ: 'M45,10 A35,35 0 1 1 44.9,10 Z' };
$('#doos').innerHTML = DOO.map(([k, x, y, c], i) => `<svg class="doo" id="d${i}" viewBox="0 0 90 90" style="left:${x}px;top:${y}px"><path d="${shp[k]}" fill="${k === 'squig' ? 'none' : c}" stroke="${k === 'squig' ? c : '#141414'}" stroke-width="${k === 'squig' ? 9 : 5}" stroke-linejoin="round" stroke-linecap="round"/></svg>`).join('');
$('#hRow').innerHTML = ['🧑‍💼', '👩‍💻', '👔', '🤖', '✏️'].map((e, i) => `<span id="hj${i}" style="width:120px;height:120px;border-radius:50%;border:6px solid #141414;box-shadow:6px 6px 0 #141414;background:${['#E6E6E3', '#fff', '#E6E6E3', '#fff', '#E6E6E3'][i]};display:flex;align-items:center;justify-content:center">${e}</span>`).join('');

function winIn(e, t, a = 0) { const k = bo(seg(t, a, a + 0.45), 1.5); css(e, { opacity: t >= a ? 1 : 0, transform: `translateY(${(1 - eo(seg(t, a, a + 0.35))) * 140}px) rotate(${lerp(-4, -1, k) + wob(t, 0.25, 0.4)}deg) scale(${lerp(0.7, 1, k)})` }); }
function head(S, t) { const k = $(`#${S} .kick`), ti = $(`#${S} .title`); if (k) pop(k, t, 0.0, '', 0.3); if (ti) pop(ti, t, 0.05, '', 0.42); }
function chipC(e, t, a) { pop(e, t, a, 'translateX(-50%)'); }
const INST = '너는 이력서 심사위원단이야. 5명이 차례로 심사해.\n① 인사 담당자: 첫인상과 읽기 쉬운지\n② 현업 팀장: 바로 일할 수 있는지\n③ 임원: 성과가 숫자로 보이는지 …';

const U = {
 hook(t) {
  pop($('#hA'), t, 0, '', 0.35); pop($('#hB'), t, 0.15, `rotate(${-1.5 + wob(t, 0.5, 0.5)}deg)`, 0.45);
  winIn($('#hRes'), t, 0.1);
  pop($('#hFree'), t, 0.0, `rotate(-8deg)`); for (let i = 0; i < 5; i++) pop($('#hj' + i), t, 1.3 + i * 0.16, `translateY(${Math.sin(t * 5 + i) * 6}px)`);
  const k = seg(t, 2.55, 2.75); css($('#hStamp'), { opacity: t >= 2.55 ? 1 : 0, transform: `rotate(-12deg) scale(${lerp(2.4, 1, eo(k))})` });
 },
 proj(t, L) { head('proj', t); winIn($('#pWin'), t, 0); pop($('#pCard'), L, 4.9, `rotate(${wob(t, 0.3, 0.8)}deg)`); chipC($('#pChip'), t, 0.6); },
 panel(t, L) { head('panel', t); [6.8, 7.3, 7.8, 8.3, 8.8].forEach((a, i) => pop($('#j' + i), L, a, `rotate(${wob(t + i, 0.4, 3)}deg)`, 0.45)); },
 score(t, L) { head('score', t); winIn($('#sCard'), t, 0.05); [7, 6, 5].forEach((v, i) => { const k = eo(seg(L, 9.4 + i * 0.25, 10.2 + i * 0.25)); $('#b' + i).style.width = v * 10 * k + '%'; $('#v' + i).textContent = Math.round(v * k) + '/10'; });
  winIn($('#rCard'), L, 10.4); [0, 1, 2].forEach((i) => css($('#r' + i), { opacity: L >= 10.6 + i * 0.4 ? 1 : 0.0 })); },
 steps(t, L) { head('steps', t); [['#n1', '#l1', 13.4], ['#n2', '#l2', 13.7], ['#n3', '#l3', 14.0]].forEach(([n, l, a]) => { pop($(n), L, a, `rotate(${wob(t + a, 0.5, 4)}deg)`, 0.4); pop($(l), L, a + 0.08); });
  const a = 12.3; const sw = L >= a ? Math.sin((L - a) * 9) * 24 * Math.exp(-(L - a) * 3) : 0; css($('#tag'), { opacity: L >= a ? 1 : 0, transform: `translateY(${(1 - eo(seg(L, a, a + 0.3))) * -300}px) rotate(${sw}deg)` }); },
 s1(t, L) { head('s1', t); winIn($('#aWin'), t, 0); const tx = 760, ty = 690; const m = eo(seg(t, 0.2, 0.7)); css($('#cur'), { left: lerp(900, tx, m) + 'px', top: lerp(1250, ty, m) + 'px', opacity: 1 });
  const r = seg(t, 0.72, 1.1); css($('#ring'), { left: tx - 20 + 'px', top: ty - 20 + 'px', opacity: r > 0 && r < 1 ? 1 - r : 0, transform: `scale(${1 + r * 3})` });
  const w = '이력서 심사위원단'; $('#pName').textContent = w.slice(0, Math.floor(cl((t - 0.8) / 0.5) * w.length)); },
 s2(t) { head('s2', t); winIn($('#bWin'), t, 0); const n = Math.floor(cl((t - 0.3) / 1.6) * INST.length); $('#inst').innerHTML = INST.slice(0, n).replace(/\n/g, '<br>'); css($('#saveBtn'), { transform: `scale(${t > 2.0 ? bo(seg(t, 2.0, 2.2)) : 1})`, background: t > 2.0 ? 'var(--v)' : 'var(--ink)' }); chipC($('#bChip'), t, 0.9); },
 s3(t) { head('s3', t); winIn($('#cWin'), t, 0); [['#f1', 0.3, 170], ['#f2', 0.75, 540]].forEach(([s, a, x]) => { const z = eo(seg(t, a, a + 0.45)); css($(s), { left: lerp(x + 200, x, z) + 'px', top: lerp(300, 880, z) - Math.sin(z * Math.PI) * 120 + 'px', opacity: t >= a ? 1 : 0, transform: `rotate(${(1 - z) * 20 - 3}deg)` }); });
  const k = seg(t, 1.5, 1.7); css($('#done'), { opacity: t >= 1.5 ? 1 : 0, transform: `rotate(-10deg) scale(${lerp(2.4, 1, eo(k))})` }); },
 ask(t) { head('ask', t); winIn($('#chat'), t, 0.05); const w = '심사해 줘'; $('#say').textContent = w.slice(0, Math.floor(cl((t - 0.2) / 0.6) * w.length)); $('#caret').style.opacity = Math.floor(t * 4) % 2 ? 0.2 : 1; const sent = t > 0.95; css($('#send'), { background: sent ? 'var(--v)' : '#fff', color: sent ? '#fff' : 'var(--ink)' });
  [...$('#res').children].forEach((c, i) => css(c, { opacity: t > 1.1 + i * 0.18 ? 1 : 0 })); },
 priv(t) { head('priv', t); winIn($('#pRes'), t, 0.05); const a = eo(seg(t, 0.5, 0.95)), b = eo(seg(t, 1.0, 1.45)); $('#rd0').style.width = a * 270 + 'px'; $('#rd1').style.width = b * 390 + 'px';
  const mx = t < 1.0 ? lerp(220, 490, a) : lerp(220, 610, b), my = t < 1.0 ? 690 : 758; css($('#marker'), { opacity: t > 0.45 && t < 1.6 ? 1 : 0, transform: `translate(${mx}px,${my}px) rotate(-8deg)` }); chipC($('#pv'), t, 1.3); },
 save(t) { head('save', t); const k = bo(seg(t, 0.1, 0.5), 2.2); css($('#bm'), { opacity: t >= 0.1 ? 1 : 0, transform: `scale(${k}, ${lerp(0.6, 1, k)}) rotate(${wob(t, 1.2, 4)}deg)` }); },
 cta(t, L) { head('cta', t); winIn($('#cbox'), t, 0.05); $('#typed').textContent = L > 27.0 ? '심사' : (L > 26.8 ? '심' : ''); $('#caret2').style.opacity = Math.floor(t * 4) % 2 ? 0.2 : 1; const b = eo(seg(L, 27.8, 28.25)); css($('#dm'), { opacity: b > 0 ? 1 : 0, transform: `translateX(${(1 - b) * 900}px) rotate(${lerp(8, 1.5, b)}deg)` }); },
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
 DOO.forEach((d, k) => css($('#d' + k), { transform: `translateY(${Math.sin(t * 1.3 + k) * 12}px) rotate(${Math.sin(t * 0.9 + k * 2) * 14}deg)` }));
 
}
window.__timelines = { main: { seek: async (t) => { render(t); }, duration: () => DUR } };
if (location.href.includes('cover')) { $('#cap').style.display = 'none'; $('#hA').textContent = '서류 내기 전에 먼저 떨어져 보기'; css($('#hA'), { fontSize: '50px', color: '#55524c', top: '250px' }); $('#hB').innerHTML = '클로드에<br><v>이력서 심사위원 5명</v>'; css($('#hB'), { fontSize: '96px', top: '330px' }); $('#hRes').style.top = '700px'; $('#hStamp').style.top = '1100px'; $('#hRow').style.top = '1290px'; }
document.fonts.ready.then(() => { render(0); window.__ready = true; });
