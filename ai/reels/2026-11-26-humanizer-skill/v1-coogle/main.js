import * as THREE from 'three';
import { RoomEnvironment } from './vendor/RoomEnvironment.js';
import { RoundedBoxGeometry } from './vendor/RoundedBoxGeometry.js';

const Q = new URLSearchParams(location.search);
const PREVIEW = Q.has('preview');
const $ = (s) => document.querySelector(s);
const F = '"Noto Sans CJK KR"';

const cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const seg = (t, a, b) => cl((t - a) / (b - a));
const expoOut = (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
const p3in = (x) => x * x * x;
const p3out = (x) => 1 - Math.pow(1 - x, 3);
const backOut = (x, s = 2.2) => 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2);
const sine = (x) => -(Math.cos(Math.PI * x) - 1) / 2;
const p4io = (x) => (x < 0.5 ? 8 * x ** 4 : 1 - Math.pow(-2 * x + 2, 4) / 2);
const lerp = (a, b, x) => a + (b - a) * x;
function rng(seed) { return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

// ---------- timeline (가안 — 녹음 받은 뒤 tl.json으로 다시 맞춤) ----------
const TL = await fetch('tl.json').then((r) => (r.ok ? r.json() : null)).catch(() => null);
const DEF = {
  dur: 31.0,
  scenes: [
    ['hook', 0, 2.9, 'split'],
    ['skill', 2.9, 6.4, 'split'],
    ['wiki', 6.4, 9.2, 'full'],
    ['zero', 9.2, 11.8, 'full'],
    ['s1', 11.8, 13.6, 'split'],
    ['s2', 13.6, 16.2, 'split'],
    ['s3', 16.2, 18.9, 'full'],
    ['diff', 18.9, 21.6, 'split'],
    ['host', 21.6, 24.2, 'host'],
    ['save', 24.2, 26.6, 'split'],
    ['profile', 26.6, 28.4, 'split'],
    ['dm', 28.4, 31.0, 'full'],
  ],
  caps: [
    [0.0, 'AI로 쓴 글,', '사람 눈엔 다 들켜요'],
    [2.9, 'AI 티 26개를', '지워 주는 스킬이 있어요'],
    [5.2, '이름은', '휴머나이저'],
    [6.4, '위키백과 편집자들이 쓰는', 'AI 글 판별법이 기준이에요'],
    [9.2, '깃허브 별이 6만 9천 개,', '스킬은 0원이에요'],
    [11.8, '첫 번째,', 'ZIP 받기'],
    [13.6, '두 번째, 사용자 정의에서', '스킬로 올리기'],
    [16.2, '세 번째, 글 붙여 넣고', "'휴머나이저로 고쳐 줘'"],
    [18.9, '뜻은 그대로 두고', '말투만 사람처럼 바꿔요'],
    [21.6, '저는 영어 메일 보내기 전에', '꼭 한 번 돌려요'],
    [24.2, '설치는 3단계예요', '저장해 두고 써요'],
    [26.6, "댓글에 '들킴' 남기면", ''],
    [28.4, '설치법', 'DM 드려요'],
  ],
};
const T = Object.assign({}, DEF, TL || {});
const SC = T.scenes.map(([id, t0, t1, lay]) => ({ id, t0, t1, lay }));

// ---------- three ----------
const canvas = $('#gl');
const R = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
R.setPixelRatio(1); R.setSize(1080, 1920, false);
R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 0.8; R.outputColorSpace = THREE.SRGBColorSpace;
const pmrem = new THREE.PMREMGenerator(R);
const scene = new THREE.Scene(); scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
const cam = new THREE.PerspectiveCamera(35, 1080 / 1920, 0.1, 200);
const key = new THREE.DirectionalLight(0xffffff, 1.3); key.position.set(-4, 6, 6); scene.add(key);
const rim = new THREE.PointLight(0xffffff, 50, 30, 1.6); rim.position.set(0, 2, -5); scene.add(rim);
scene.add(new THREE.AmbientLight(0xffffff, 0.05)); scene.fog = new THREE.FogExp2(0x07080a, 0.05);

function ctex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); draw(g, w, h); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; }
const rr = (g, x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };

// AI 티 패턴 타일 (README 범주를 한국어로 짧게 — 화면용 요약)
const TELLS = ['"단순한 X가 아니라 Y"', '"결론적으로"', '줄표 — 남발', '셋씩 나열', '깊어 보이는 말', '"Let that sink in."', '과장된 의미 부여', '연출된 도입', '빌려 온 권위', '규칙적인 리듬', '굵은 글씨 남발', '대화 찌꺼기', '아무도 안 한 반박', '겹친 완화 표현', '이모지 제목', '"I hope this finds you well"'];
function tileTex(i, struck) {
  return ctex(640, 200, (g, w, h) => {
    g.fillStyle = '#f5f5f7'; rr(g, 4, 4, w - 8, h - 8, 34); g.fill();
    g.fillStyle = '#111'; g.font = `900 30px ${F}`; g.fillText(String(i + 1).padStart(2, '0'), 34, 62);
    g.font = `800 44px ${F}`; const s = TELLS[i % TELLS.length]; g.fillText(s, 34, 140);
    if (struck) { const m = g.measureText(s).width; g.fillStyle = '#111'; g.fillRect(28, 122, m + 14, 8); }
  });
}
const tiles = []; { const r = rng(5); const geo = new RoundedBoxGeometry(2.0, 0.62, 0.04, 4, 0.06); const g = new THREE.Group(); g.visible = false; scene.add(g);
  for (let i = 0; i < 26; i++) { const mat = new THREE.MeshStandardMaterial({ map: tileTex(i, false), roughness: 0.45, metalness: 0.05, emissive: 0xffffff, emissiveIntensity: 0.12 }); mat.userData = { plain: mat.map, struck: tileTex(i, true) };
    const m = new THREE.Mesh(geo, mat); const a = r() * Math.PI * 2, rad = 1.2 + r() * 3.2;
    m.userData = { p: new THREE.Vector3(Math.cos(a) * rad * 1.1, (r() - 0.5) * 6, -2 - r() * 8), rot: new THREE.Euler((r() - 0.5) * 0.6, (r() - 0.5) * 0.9, (r() - 0.5) * 0.5), v: new THREE.Vector3((r() - 0.5) * 3, (r() - 0.3) * 3, 5 + r() * 6), spin: (r() - 0.5) * 5, a: (i / 26) * Math.PI * 2, orad: 3.0 + r() * 1.2, y: (r() - 0.5) * 3.2, sp: 0.5 + r() * 0.4 };
    g.add(m); tiles.push(m); }
  var tileG = g; }

// 위키 가이드 슬랩 (텍스트만, 로고 없음)
function slabTex() {
  return ctex(768, 1024, (g, w, h) => {
    g.fillStyle = '#f7f7f8'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#111'; g.font = `400 34px serif`; g.fillText('Wikipedia', 56, 86);
    g.fillStyle = '#000'; g.font = `700 52px serif`; g.fillText('Signs of AI writing', 56, 170);
    g.fillStyle = '#a2a9b1'; g.fillRect(56, 196, w - 112, 2);
    g.fillStyle = '#54595d'; g.font = `500 26px ${F}`; g.fillText('WikiProject AI Cleanup', 56, 250);
    for (let i = 0; i < 16; i++) { g.fillStyle = i % 4 === 0 ? '#202122' : '#c8ccd1'; g.fillRect(56, 310 + i * 42, i % 4 === 0 ? 300 : 360 + ((i * 53) % 260), i % 4 === 0 ? 20 : 14); }
  });
}
const slabG = new THREE.Group(); slabG.visible = false; scene.add(slabG);
const slab = new THREE.Mesh(new RoundedBoxGeometry(3.0, 4.0, 0.16, 6, 0.1), new THREE.MeshPhysicalMaterial({ color: 0xdedfe3, roughness: 0.3, metalness: 0.2, clearcoat: 1 }));
const slabFace = new THREE.Mesh(new THREE.PlaneGeometry(2.86, 3.82), new THREE.MeshStandardMaterial({ map: slabTex(), emissive: 0xffffff, emissiveMap: slabTex(), emissiveIntensity: 0.35, roughness: 0.5 }));
slabFace.position.z = 0.085; slab.add(slabFace); slabG.add(slab);
const halo = new THREE.Mesh(new THREE.PlaneGeometry(7, 8), new THREE.MeshBasicMaterial({ map: ctex(256, 256, (g) => { const rg = g.createRadialGradient(128, 128, 0, 128, 128, 128); rg.addColorStop(0, 'rgba(255,255,255,.55)'); rg.addColorStop(0.4, 'rgba(200,200,210,.18)'); rg.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = rg; g.fillRect(0, 0, 256, 256); }), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
halo.position.z = -0.8; slabG.add(halo);

// 북마크
const bmG = new THREE.Group(); bmG.visible = false; scene.add(bmG);
{ const s = new THREE.Shape(); s.moveTo(-0.6, 0.9); s.lineTo(0.6, 0.9); s.lineTo(0.6, -0.9); s.lineTo(0, -0.45); s.lineTo(-0.6, -0.9); s.closePath(); const geo = new THREE.ExtrudeGeometry(s, { depth: 0.25, bevelEnabled: true, bevelThickness: 0.06, bevelSize: 0.05, bevelSegments: 4 }); geo.center(); bmG.add(new THREE.Mesh(geo, new THREE.MeshPhysicalMaterial({ color: 0xf5f5f7, roughness: 0.22, metalness: 0.15, clearcoat: 1 }))); }

// dust
const dustG = new THREE.BufferGeometry(); { const r = rng(7); const n = 240; const p = new Float32Array(n * 3); for (let i = 0; i < n; i++) { p[i * 3] = (r() - 0.5) * 16; p[i * 3 + 1] = (r() - 0.5) * 22; p[i * 3 + 2] = -8 + r() * 12; } dustG.setAttribute('position', new THREE.BufferAttribute(p, 3)); }
const dust = new THREE.Points(dustG, new THREE.PointsMaterial({ size: 0.05, map: ctex(64, 64, (g) => { const rg = g.createRadialGradient(32, 32, 0, 32, 32, 32); rg.addColorStop(0, '#fff'); rg.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = rg; g.fillRect(0, 0, 64, 64); }), transparent: true, opacity: 0.4, depthWrite: false, blending: THREE.AdditiveBlending }));
scene.add(dust);

// ---------- DOM ----------
const layers = [...document.querySelectorAll('.layer')];
const empty = document.createElement('div'); empty.className = 'layer'; empty.id = 'L_none'; $('#dom').appendChild(empty); layers.push(empty);
const show = (id) => layers.forEach((l) => (l.style.visibility = l.id === id ? 'visible' : 'hidden'));
const css = (el, o) => Object.assign(el.style, o);
{ const z = $('#zero'); for (let i = 13; i >= 0; i--) { const d = document.createElement('div'); d.className = 'z'; d.textContent = '0원'; d.style.transform = `translateZ(${-i * 2.2}px)`; d.style.color = i === 0 ? '#F5F5F7' : `color-mix(in srgb,#5a5d66 ${100 - i * 6}%,#07080A)`; z.appendChild(d); } }
const bctx = $('#bloom').getContext('2d');

const capEl = $('#cap'); let lastCap = -1;
function captions(t, lay) {
  let i = -1; for (let k = 0; k < T.caps.length; k++) if (t >= T.caps[k][0]) i = k;
  const c = T.caps[i]; if (!c) { capEl.innerHTML = ''; return; }
  if (i !== lastCap) { capEl.innerHTML = `<div class="l1">${c[1]}</div>${c[2] ? `<div class="l2">${c[2]}</div>` : ''}`; lastCap = i; }
  const lt = t - c[0];
  capEl.style.top = lay === 'split' ? (c[2] ? '842px' : '890px') : lay === 'host' ? '1380px' : '1400px';
  const l1 = capEl.querySelector('.l1'), l2 = capEl.querySelector('.l2');
  const a = expoOut(seg(lt, 0, 0.35)); css(l1, { opacity: a, transform: `translateY(${(1 - a) * 14}px)` });
  if (l2) { const b = expoOut(seg(lt, 0.2, 0.55)); css(l2, { opacity: b, transform: `translateY(${(1 - b) * 14}px) scale(${lerp(0.94, 1, b)})` }); }
}
function steps(n) { const s = $('#steps'); s.style.display = n ? 'flex' : 'none'; [...s.children].forEach((d, i) => d.classList.toggle('on', i + 1 === n)); }
function fx(o = {}) { $('#flash').style.opacity = Math.max(o.flash || 0, (o.flashIn || 0) * 0.8); $('#dip').style.opacity = o.dip || 0; const w = o.whip || 0; canvas.style.transform = w ? `translateX(${-w * 260}px)` : ''; canvas.style.filter = w > 0.01 ? `blur(${w * 36}px)` : ''; $('#dom').style.filter = w > 0.01 ? `blur(${w * 30}px)` : ''; }

const U = {
  hook(t, d) {
    show('L_hook'); tileG.visible = true;
    cam.position.set(0, 0.2, lerp(9, 6.4, sine(seg(t, 0, d)))); cam.lookAt(0, 0.2, -3);
    const blow = seg(t, 1.9, d);
    tiles.forEach((m, i) => { const u = m.userData; const f = p3in(blow); const st = t > 0.9 + (i % 6) * 0.12; m.material.map = st ? m.material.userData.struck : m.material.userData.plain;
      m.position.set(u.p.x + u.v.x * f, u.p.y + Math.sin(t * 0.7 + i) * 0.08 + u.v.y * f, u.p.z + u.v.z * f); m.rotation.set(u.rot.x + t * 0.05 + u.spin * f, u.rot.y + t * 0.06 + u.spin * f, u.rot.z); m.material.transparent = f > 0; m.material.opacity = 1 - f; });
    const a = expoOut(seg(t, 0, 0.3)); css($('#hookT'), { opacity: 0.999 * (1 - seg(t, d - 0.2, d)) + 0.001, transform: `translateY(${(1 - a) * 0}px) scale(${lerp(1.04, 1, sine(seg(t, 0, d)))})` });
    css($('#hookChip'), { transform: `scale(${1 + Math.exp(-Math.pow((t - 0.7) / 0.12, 2)) * 0.08})`, opacity: 1 - seg(t, d - 0.2, d) });
    fx({ dip: seg(t, d - 0.12, d) });
  },
  wiki(t, d) {
    show('L_wiki'); slabG.visible = true; tileG.visible = true;
    const k = seg(t, 0, d); const ang = lerp(-0.3, 0.25, sine(k)); cam.position.set(Math.sin(ang) * 11, lerp(2.4, 1.4, k), Math.cos(ang) * 11); cam.lookAt(0, 0.3, 0);
    slabG.position.set(0, 0.4, 0); slabG.rotation.set(-0.1, Math.sin(t * 0.5) * 0.08, 0); slabG.scale.setScalar(lerp(0.6, 0.85, expoOut(seg(t, 0, 0.6))));
    tiles.forEach((m, i) => { const u = m.userData; m.material.map = m.material.userData.plain; m.material.opacity = 1; m.material.transparent = false; const ent = expoOut(seg(t, 0.3 + i * 0.03, 0.9 + i * 0.03)); const a = u.a + t * u.sp * 0.7; const rad = lerp(10, u.orad, ent); m.position.set(Math.cos(a) * rad, 0.3 + u.y, Math.sin(a) * rad * 0.7); m.lookAt(cam.position); m.scale.setScalar(0.7); });
    const c = backOut(seg(t, 1.0, 1.4)); css($('#wikiChip'), { transform: `translateX(-50%) scale(${c})`, opacity: seg(t, 1.0, 1.1) });
    fx({ flashIn: 1 - seg(t, 0, 0.12), whip: seg(t, d - 0.2, d) });
  },
  skill(t, d) {
    show('L_skill'); const c = $('#repo'); const a = expoOut(seg(t, 0, 0.55));
    css(c, { transform: `translateY(${(1 - a) * 80}px) rotateX(${lerp(14, 4, a)}deg) rotateY(${-5 + sine(seg(t, 0, d)) * 6}deg)`, opacity: a });
    $('#starN').textContent = (lerp(0, 69.3, p3out(seg(t, 0.4, 1.6)))).toFixed(1) + 'k';
    $('#hlRead').style.background = `rgba(255,255,255,${0.22 * seg(t, 1.6, 2.0)})`;
  },
  zero(t, d) {
    show('L_zero'); const z = $('#zero'); const a = backOut(seg(t, 0.1, 0.5));
    css(z, { transform: `translateZ(${lerp(-900, 0, a)}px) rotateY(${lerp(-18, -6, sine(seg(t, 0, d)))}deg) rotateX(6deg)`, opacity: seg(t, 0.1, 0.18) });
    const b = backOut(seg(t, 0.55, 0.9)); css($('#zeroChip'), { transform: `translateX(-50%) scale(${b})`, opacity: seg(t, 0.55, 0.65) });
    fx({ flash: Math.exp(-Math.pow((t - 0.5) / 0.06, 2)) * 0.5 });
  },
  s1(t, d) {
    show('L_s1'); steps(1); const a = expoOut(seg(t, 0, 0.45)); css($('#bd1'), { opacity: a, transform: `translateX(${(1 - a) * -60}px)` });
    css($('#zipCard'), { transform: `rotateX(${lerp(12, 4, a)}deg) rotateY(${3 - sine(seg(t, 0, d)) * 5}deg) scale(${lerp(0.95, 1, a)})`, opacity: a });
    const open = t > 0.55; $('#dd').style.display = open ? 'block' : 'none';
    $('#dlZip').style.background = t > 0.95 ? '#e6edf3' : 'transparent'; $('#dlZip').style.color = t > 0.95 ? '#0d1117' : '#e6edf3';
    const cx = t < 0.55 ? lerp(700, 850, p4io(seg(t, 0.1, 0.5))) : lerp(850, 760, p4io(seg(t, 0.6, 0.95))); const cy = t < 0.55 ? lerp(560, 300, p4io(seg(t, 0.1, 0.5))) : lerp(300, 520, p4io(seg(t, 0.6, 0.95)));
    const click = Math.sin(Math.PI * seg(t, 0.45, 0.6)) + Math.sin(Math.PI * seg(t, 0.92, 1.05)); css($('#cursor'), { left: cx + 'px', top: cy + 'px', transform: `scale(${1 - click * 0.15})` });
    const dl = seg(t, 1.1, d - 0.15); $('#dlBar').style.opacity = dl > 0 ? 1 : 0; $('#dlP').style.width = p3out(dl) * 100 + '%';
  },
  s2(t, d) {
    show('L_s2'); steps(2); const a = expoOut(seg(t, 0, 0.45)); css($('#bd2'), { opacity: a, transform: `translateX(${(1 - a) * -60}px)` });
    css($('#setCard'), { transform: `rotateX(${lerp(12, 4, a)}deg) rotateY(${-3 + sine(seg(t, 0, d)) * 5}deg) scale(${lerp(0.95, 1, a)})`, opacity: a });
    const f = p3in(seg(t, 0.5, 1.0)); css($('#zipFly'), { top: lerp(-140, 150, f) + 'px', opacity: 1 - seg(t, 0.95, 1.05), transform: `rotate(${lerp(-12, 0, f)}deg)` });
    const on = t > 1.3; $('#tg').classList.toggle('on', on); $('#skRow').style.opacity = t > 1.0 ? 1 : 0; $('#skRow').style.transform = `translateY(${(1 - expoOut(seg(t, 1.0, 1.3))) * -20}px)`;
  },
  s3(t, d) {
    show('L_s3'); steps(3); tileG.visible = true; const a = expoOut(seg(t, 0, 0.45)); css($('#bd3'), { opacity: a, transform: `translateX(${(1 - a) * -60}px)` });
    cam.position.set(lerp(-1, 1, sine(seg(t, 0, d))), 0.6, 9); cam.lookAt(0, 0.6, 0);
    const word = '휴머나이저로 고쳐 줘'; const n = Math.floor(seg(t, 0.3, 1.2) * (word.length + 0.99)); $('#askT').textContent = word.slice(0, n); $('#caret2').style.opacity = Math.floor(t * 4) % 2 ? 0.2 : 1;
    const go = seg(t, 1.4, d);
    tiles.forEach((m, i) => { if (i > 11) { m.visible = false; return; } m.visible = true; const u = m.userData; const col = i % 2, row = Math.floor(i / 2); const bx = col ? 1.15 : -1.15, by = 2.6 - row * 0.72; const f = p3in(seg(go, (i % 6) * 0.05, 0.6 + (i % 6) * 0.05));
      m.material.map = t > 1.3 + (i % 4) * 0.06 ? m.material.userData.struck : m.material.userData.plain; m.scale.setScalar(0.52);
      m.position.set(bx + u.v.x * f * 0.8, by + u.v.y * f * 0.6, u.v.z * f); m.rotation.set(u.spin * f, -col * 0.1 + 0.05 + u.spin * f, 0); m.lookAt(cam.position.x, cam.position.y, 20); m.rotation.z += u.spin * f; m.material.transparent = f > 0; m.material.opacity = 1 - f; });
    fx({ flashIn: 1 - seg(t, 0, 0.12) });
  },
  diff(t, d) {
    show('L_diff'); const a = expoOut(seg(t, 0, 0.5)); css($('#before'), { transform: `rotateY(${lerp(18, 10, a)}deg) translateX(${(1 - a) * -80}px)`, opacity: a, filter: `blur(${seg(t, 1.1, 1.5) * 2}px)` });
    const b = expoOut(seg(t, 0.6, 1.1)); css($('#after'), { transform: `rotateY(${lerp(-24, -6, b)}deg) translateZ(${lerp(-200, 40, b)}px)`, opacity: b });
  },
  host() { show('L_none'); },
  save(t, d) {
    show('L_save'); bmG.visible = true; cam.position.set(0, 0, 7); cam.lookAt(0, 0, 0);
    const k = seg(t, 0, 0.32); const y = lerp(2.0, -0.25, p3in(k)) + (k >= 1 ? 0.22 * Math.abs(Math.sin((t - 0.32) * 10)) * Math.exp(-(t - 0.32) * 5) : 0);
    bmG.position.set(0, y + 0.2, 0); bmG.scale.setScalar(0.6); bmG.rotation.set(0.12, Math.sin(t * 2.2) * 0.45, 0.04);
    const b = backOut(seg(t, 0.3, 0.6)); css($('#saveChip'), { transform: `translateX(-50%) scale(${b})`, opacity: seg(t, 0.3, 0.38) });
  },
  profile(t, d) {
    show('L_profile'); const a = expoOut(seg(t, 0, 0.5)); css($('#prof'), { transform: `rotateX(${lerp(12, 4, a)}deg) rotateY(${2 - sine(seg(t, 0, d)) * 4}deg) translateY(${(1 - a) * 60}px)`, opacity: a });
    const f = t > 0.9; const btn = $('#fBtn'); btn.textContent = f ? '팔로잉' : '팔로우'; css(btn, { background: f ? 'rgba(255,255,255,.12)' : 'var(--paper)', color: f ? 'var(--paper)' : 'var(--ink)', transform: `scale(${1 - Math.sin(Math.PI * seg(t, 0.75, 0.95)) * 0.05})` });
    fx({ flash: seg(t, d - 0.1, d) * 0.5 });
  },
  dm(t, d) {
    show('L_dm'); const a = expoOut(seg(t, 0, 0.5)); css($('#cmt'), { transform: `rotateX(${lerp(14, 5, a)}deg) translateY(${(1 - a) * 60}px)`, opacity: a });
    const word = '들킴'; const n = Math.floor(seg(t, 0.35, 0.8) * (word.length + 0.99)); $('#typed').textContent = word.slice(0, n); $('#caret').style.opacity = Math.floor(t * 4) % 2 ? 0.2 : 1;
    const b = expoOut(seg(t, 1.1, 1.65)); css($('#dm'), { transform: `perspective(1400px) rotateY(${lerp(-70, -6, b)}deg) translateX(${(1 - b) * 300}px)`, opacity: b });
    fx({ flashIn: 1 - seg(t, 0, 0.12) });
  },
};

function render(t) {
  const s = SC.find((x) => t >= x.t0 && t < x.t1) || SC[SC.length - 1];
  const lt = t - s.t0, d = s.t1 - s.t0;
  $('#stage').className = 'stage ' + (s.lay === 'split' ? 'split' : s.lay === 'host' ? 'hostonly' : '');
  $('#seam').style.display = s.lay === 'split' ? 'block' : 'none';
  const host = $('#host'); if (PREVIEW) { host.style.display = s.lay === 'full' ? 'none' : 'block'; css(host, s.lay === 'split' ? { top: '960px', height: '960px' } : { top: '0px', height: '1920px' }); }
  [tileG, slabG, bmG].forEach((g) => (g.visible = false)); tiles.forEach((m) => { m.visible = true; m.scale.setScalar(1); });
  steps(0); fx({});
  if (s.lay === 'split') { R.setViewport(0, 960, 1080, 960); R.setScissor(0, 960, 1080, 960); R.setScissorTest(true); cam.aspect = 1080 / 960; } else { R.setViewport(0, 0, 1080, 1920); R.setScissorTest(false); cam.aspect = 1080 / 1920; }
  cam.fov = s.lay === 'split' ? 30 : 35; cam.updateProjectionMatrix();
  dust.position.y = Math.sin(t * 0.2) * 0.3; dust.rotation.y = t * 0.02;
  U[s.id] && U[s.id](lt, d, s);
  R.setClearColor(0x000000, 0); R.clear(); R.render(scene, cam);
  bctx.clearRect(0, 0, 540, 960); bctx.drawImage(canvas, 0, 0, 540, 960);
  $('#turb').setAttribute('seed', String(Math.floor(t * 30) % 97));
  captions(t, s.lay);
  $('#brand').style.opacity = s.lay === 'host' ? 0 : 0.9;
}
await document.fonts.ready;
window.__timelines = { main: { seek: (t) => render(t), duration: () => T.dur } };
window.__T = T; window.__ready = true;
render(Number(Q.get('t') || 0));
