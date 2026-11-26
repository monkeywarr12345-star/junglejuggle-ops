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
    ['hook', 0, 3.0, 'split'],
    ['policy', 3.0, 5.8, 'split'],
    ['raw', 5.8, 8.8, 'split'],
    ['three', 8.8, 10.6, 'full'],
    ['s1', 10.6, 13.8, 'split'],
    ['s2', 13.8, 17.0, 'split'],
    ['s3', 17.0, 20.6, 'split'],
    ['trap', 20.6, 23.0, 'full'],
    ['host', 23.0, 25.0, 'host'],
    ['save', 25.0, 27.4, 'split'],
    ['profile', 27.4, 29.0, 'split'],
    ['dm', 29.0, 31.0, 'full'],
  ],
  caps: [
    [0.0, '검색에 지메일 연결했다면,', '광고에 쓰일 수 있어요'],
    [3.0, '구글이 10월 16일', '개인정보처리방침을 바꿨거든요'],
    [5.8, '광고주한텐 메일이 안 가지만', '요약·추론은 쓰일 수 있어요'],
    [8.8, '끄는 곳은', '세 군데예요'],
    [10.6, '첫 번째, 검색 맞춤설정에서', '연결된 앱 끊기'],
    [13.8, '두 번째, 내 광고 센터에서', '맞춤 광고 끄기'],
    [17.0, '세 번째, 제미나이 연결된 앱', '설정이 따로라 같이 정리해요'],
    [20.6, '하나만 끄면', '나머지는 그대로예요'],
    [23.0, '저도 세 개', '다 꺼 뒀어요'],
    [25.0, '메뉴 위치 까먹기 쉬워요', '저장해 두고 꺼요'],
    [27.4, "댓글에 '끄기' 남기면", ''],
    [29.0, '끄는 법', 'DM 드려요'],
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

// 데이터 조각: 메일 봉투 / 사진 타일 (흑백)
const MAILS = ['항공권 예약 확인', '주문하신 상품 발송', '호텔 예약 안내', '청첩장 도착', '헬스장 등록 완료', '렌터카 영수증', '이사 견적서', '강의 수강 안내'];
function mailTex(i) {
  return ctex(512, 340, (g, w, h) => {
    g.fillStyle = '#f5f5f7'; rr(g, 4, 4, w - 8, h - 8, 26); g.fill();
    g.strokeStyle = '#c4c7cf'; g.lineWidth = 6; g.beginPath(); g.moveTo(18, 24); g.lineTo(w / 2, 170); g.lineTo(w - 18, 24); g.stroke();
    g.fillStyle = '#111'; g.font = `900 26px ${F}`; g.fillText('Gmail', 34, 250);
    g.font = `800 34px ${F}`; g.fillText(MAILS[i % MAILS.length], 34, 300);
  });
}
function photoTex(i) {
  return ctex(400, 400, (g, w, h) => {
    g.fillStyle = '#f5f5f7'; rr(g, 4, 4, w - 8, h - 8, 26); g.fill();
    const r = rng(i + 11); const gr = g.createLinearGradient(0, 30, 0, 310); const a = 60 + r() * 80; gr.addColorStop(0, `rgb(${a},${a},${a + 6})`); gr.addColorStop(1, `rgb(${a + 90},${a + 90},${a + 96})`);
    g.fillStyle = gr; rr(g, 26, 26, w - 52, 290, 16); g.fill();
    g.fillStyle = 'rgba(255,255,255,.55)'; g.beginPath(); g.arc(90 + r() * 200, 100, 30, 0, 7); g.fill();
    g.fillStyle = '#2a2c31'; g.beginPath(); g.moveTo(26, 316); g.lineTo(150 + r() * 60, 170); g.lineTo(260, 316); g.fill();
    g.fillStyle = '#111'; g.font = `900 28px ${F}`; g.fillText('Photos', 30, 368);
  });
}
const bits = []; const bitG = new THREE.Group(); bitG.visible = false; scene.add(bitG);
{ const r = rng(5); const gm = new RoundedBoxGeometry(1.5, 1.0, 0.05, 4, 0.06), gp = new RoundedBoxGeometry(1.1, 1.1, 0.05, 4, 0.06);
  for (let i = 0; i < 22; i++) { const isMail = i % 2 === 0; const mat = new THREE.MeshStandardMaterial({ map: isMail ? mailTex(i / 2) : photoTex(i), roughness: 0.45, metalness: 0.05, emissive: 0xffffff, emissiveIntensity: 0.1 });
    const m = new THREE.Mesh(isMail ? gm : gp, mat); const a = r() * Math.PI * 2;
    m.userData = { a, orad: 2.6 + r() * 2.2, y: (r() - 0.5) * 5.5, z: -1 - r() * 6, sp: 0.35 + r() * 0.35, rot: new THREE.Euler((r() - 0.5) * 0.6, (r() - 0.5) * 0.9, (r() - 0.5) * 0.5), spin: (r() - 0.5) * 3, d: r() };
    bitG.add(m); bits.push(m); } }

// 광고판 슬랩 (AD)
function adTex() {
  return ctex(768, 1024, (g, w, h) => {
    g.fillStyle = '#f7f7f8'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#111'; rr(g, 56, 60, 130, 60, 12); g.fill(); g.fillStyle = '#fff'; g.font = `900 38px ${F}`; g.fillText('광고', 80, 104);
    g.fillStyle = '#111'; g.font = `900 64px ${F}`; g.fillText('제주 항공권', 56, 230); g.fillText('특가 알림', 56, 310);
    g.fillStyle = '#9ca0ab'; g.font = `600 30px ${F}`; g.fillText('내 관심사에 맞춘 광고', 56, 370);
    g.fillStyle = '#d6d8de'; rr(g, 56, 420, w - 112, 380, 22); g.fill();
    g.fillStyle = '#b8bbc3'; g.beginPath(); g.moveTo(56, 800); g.lineTo(300, 560); g.lineTo(520, 800); g.fill();
    g.fillStyle = '#111'; rr(g, 56, 850, w - 112, 110, 55); g.fill(); g.fillStyle = '#fff'; g.font = `900 42px ${F}`; g.fillText('지금 보기', w / 2 - 90, 920);
  });
}
const adG = new THREE.Group(); adG.visible = false; scene.add(adG);
const adSlab = new THREE.Mesh(new RoundedBoxGeometry(3.0, 4.0, 0.16, 6, 0.1), new THREE.MeshPhysicalMaterial({ color: 0xdedfe3, roughness: 0.3, metalness: 0.2, clearcoat: 1 }));
const adFace = new THREE.Mesh(new THREE.PlaneGeometry(2.86, 3.82), new THREE.MeshStandardMaterial({ map: adTex(), emissive: 0xffffff, emissiveMap: adTex(), emissiveIntensity: 0.35, roughness: 0.5 }));
adFace.position.z = 0.085; adSlab.add(adFace); adG.add(adSlab);
const halo = new THREE.Mesh(new THREE.PlaneGeometry(7, 8), new THREE.MeshBasicMaterial({ map: ctex(256, 256, (g) => { const rg = g.createRadialGradient(128, 128, 0, 128, 128, 128); rg.addColorStop(0, 'rgba(255,255,255,.55)'); rg.addColorStop(0.4, 'rgba(200,200,210,.18)'); rg.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = rg; g.fillRect(0, 0, 256, 256); }), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
halo.position.z = -0.8; adG.add(halo);

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
{ const z = $('#zero'); for (let i = 13; i >= 0; i--) { const d = document.createElement('div'); d.className = 'z'; d.textContent = '3곳'; d.style.transform = `translateZ(${-i * 2.2}px)`; d.style.color = i === 0 ? '#F5F5F7' : `color-mix(in srgb,#5a5d66 ${100 - i * 6}%,#07080A)`; z.appendChild(d); } }
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
const tog = (el, on) => el.classList.toggle('on', on);

// 데이터 조각이 광고판으로 빨려 들어감 (k: 0 궤도 → 1 흡수)
function orbitBits(t, k, scale = 0.62) {
  bits.forEach((m, i) => { const u = m.userData; const a = u.a + t * u.sp; const f = p3in(cl(k * 1.6 - u.d * 0.6));
    const ox = Math.cos(a) * u.orad, oy = u.y, oz = Math.sin(a) * u.orad * 0.6 + u.z * 0.3;
    m.position.set(lerp(ox, 0, f), lerp(oy, 0.4, f), lerp(oz, 0.2, f)); m.rotation.set(u.rot.x + t * 0.08 + u.spin * f, u.rot.y + t * 0.1 + u.spin * f, u.rot.z);
    m.scale.setScalar(scale * (1 - f * 0.9)); m.material.transparent = f > 0; m.material.opacity = 1 - f; });
}

const U = {
  hook(t, d) {
    show('L_hook'); bitG.visible = true; adG.visible = true;
    cam.position.set(Math.sin(t * 0.25) * 1.2, 0.3, lerp(11, 9, sine(seg(t, 0, d)))); cam.lookAt(0, 0.3, 0);
    adG.position.set(0, 0.4, -1.2); adG.rotation.set(-0.05, Math.sin(t * 0.6) * 0.12, 0); adG.scale.setScalar(lerp(0.55, 0.7, sine(seg(t, 0, d))));
    orbitBits(t, seg(t, 0.8, d));
    css($('#hookT'), { opacity: 0.999 * (1 - seg(t, d - 0.2, d)) + 0.001, transform: `scale(${lerp(1.04, 1, sine(seg(t, 0, d)))})` });
    css($('#hookChip'), { transform: `scale(${1 + Math.exp(-Math.pow((t - 0.7) / 0.12, 2)) * 0.08})`, opacity: 1 - seg(t, d - 0.2, d) });
    fx({ dip: seg(t, d - 0.12, d) });
  },
  policy(t, d) {
    show('L_policy'); const a = expoOut(seg(t, 0, 0.55));
    css($('#pol'), { transform: `translateY(${(1 - a) * 80}px) rotateX(${lerp(14, 4, a)}deg) rotateY(${-5 + sine(seg(t, 0, d)) * 6}deg)`, opacity: a });
    const h = seg(t, 0.9, 1.9); $('#hlPol').style.background = `linear-gradient(90deg,rgba(17,17,17,.14) ${h * 100}%,transparent ${h * 100}%)`;
    const b = backOut(seg(t, 2.0, 2.35)); css($('#newTag'), { transform: `scale(${b})`, opacity: seg(t, 2.0, 2.08) });
    css($('#effd'), { transform: `scale(${1 + Math.exp(-Math.pow((t - 0.6) / 0.1, 2)) * 0.12})` });
  },
  flow(t, d) {
    show('L_flow'); bitG.visible = true; adG.visible = true;
    const k = seg(t, 0, d); const ang = lerp(-0.35, 0.25, sine(k)); cam.position.set(Math.sin(ang) * 11, lerp(2.2, 1.2, k), Math.cos(ang) * 11); cam.lookAt(0, 0.5, 0);
    adG.position.set(0, 0.6, 0); adG.rotation.set(-0.08, Math.sin(t * 0.5) * 0.1, 0); adG.scale.setScalar(lerp(0.55, 0.9, expoOut(seg(t, 0, 0.7))));
    orbitBits(t + 3, seg(t, 0.5, d - 0.3), 0.75);
    const c = backOut(seg(t, 0.9, 1.3)); css($('#flowChip'), { transform: `translateX(-50%) scale(${c})`, opacity: seg(t, 0.9, 1.0) });
    const c2 = backOut(seg(t, 1.5, 1.85)); css($('#flowSub'), { transform: `translateX(-50%) scale(${c2})`, opacity: seg(t, 1.5, 1.6) });
    fx({ flashIn: 1 - seg(t, 0, 0.12), whip: seg(t, d - 0.2, d) });
  },
  raw(t, d) {
    show('L_raw'); const a = expoOut(seg(t, 0, 0.5)); css($('#rawA'), { transform: `rotateY(${lerp(18, 10, a)}deg) translateX(${(1 - a) * -80}px)`, opacity: a, filter: `blur(${seg(t, 1.3, 1.7) * 1.5}px)` });
    css($('#xMark'), { transform: `scale(${backOut(seg(t, 0.5, 0.8))})` });
    const b = expoOut(seg(t, 0.9, 1.4)); css($('#rawB'), { transform: `rotateY(${lerp(-24, -6, b)}deg) translateZ(${lerp(-200, 40, b)}px)`, opacity: b });
    css($('#oMark'), { transform: `scale(${backOut(seg(t, 1.5, 1.8))})` });
  },
  host() { show('L_none'); },
  three(t, d) {
    show('L_three'); const z = $('#zero'); const a = backOut(seg(t, 0.1, 0.5));
    css(z, { transform: `translateZ(${lerp(-900, 0, a)}px) rotateY(${lerp(-18, -6, sine(seg(t, 0, d)))}deg) rotateX(6deg)`, opacity: seg(t, 0.1, 0.18) });
    const b = backOut(seg(t, 0.6, 0.95)); css($('#zeroChip'), { transform: `translateX(-50%) scale(${b})`, opacity: seg(t, 0.6, 0.7) });
    fx({ flash: Math.exp(-Math.pow((t - 0.5) / 0.06, 2)) * 0.5 });
  },
  s1(t, d) {
    show('L_s1'); steps(1); const a = expoOut(seg(t, 0, 0.45)); css($('#bd1'), { opacity: a, transform: `translateX(${(1 - a) * -60}px)` });
    css($('#c1'), { transform: `rotateX(${lerp(12, 4, a)}deg) rotateY(${3 - sine(seg(t, 0, d)) * 5}deg) scale(${lerp(0.95, 1, a)})`, opacity: a });
    tog($('#t1a'), t < 1.0); tog($('#t1b'), t < 1.7);
    const cx = t < 1.0 ? lerp(620, 860, p4io(seg(t, 0.3, 0.9))) : 860; const cy = t < 1.0 ? lerp(780, 470, p4io(seg(t, 0.3, 0.9))) : lerp(470, 590, p4io(seg(t, 1.1, 1.6)));
    const click = Math.sin(Math.PI * seg(t, 0.9, 1.05)) + Math.sin(Math.PI * seg(t, 1.6, 1.75)); css($('#cursor'), { left: cx + 'px', top: cy + 'px', transform: `scale(${1 - click * 0.15})` });
  },
  s2(t, d) {
    show('L_s2'); steps(2); const a = expoOut(seg(t, 0, 0.45)); css($('#bd2'), { opacity: a, transform: `translateX(${(1 - a) * -60}px)` });
    css($('#c2'), { transform: `rotateX(${lerp(12, 4, a)}deg) rotateY(${3 - sine(seg(t, 0, d)) * 5}deg) scale(${lerp(0.95, 1, a)})`, opacity: a });
    const off = t > 1.2; tog($('#t2'), !off); $('#adState').textContent = off ? '사용 안 함' : '사용 중';
  },
  s3(t, d) {
    show('L_s3'); steps(3); const a = expoOut(seg(t, 0, 0.45)); css($('#bd3'), { opacity: a, transform: `translateX(${(1 - a) * -60}px)` });
    css($('#c3'), { transform: `rotateX(${lerp(12, 4, a)}deg) rotateY(${-3 + sine(seg(t, 0, d)) * 5}deg) scale(${lerp(0.95, 1, a)})`, opacity: a });
    tog($('#t3a'), t < 1.0); tog($('#t3b'), t < 1.4);
    const b = backOut(seg(t, 1.6, 1.95)); css($('#sepChip'), { transform: `translateX(-50%) scale(${b})`, opacity: seg(t, 1.6, 1.7) });
  },
  trap(t, d) {
    show('L_trap'); const a = expoOut(seg(t, 0, 0.5)); css($('#sws'), { transform: `rotateX(${lerp(20, 8, a)}deg) translateY(${(1 - a) * 80}px)`, opacity: a });
    $('#b2').classList.toggle('off', t > 1.2); $('#b3').classList.toggle('off', t > 1.45);
    const b = backOut(seg(t, 1.5, 1.85)); css($('#trapChip'), { transform: `translateX(-50%) scale(${b})`, opacity: seg(t, 1.5, 1.6) });
    fx({ flashIn: 1 - seg(t, 0, 0.12) });
  },
  save(t, d) {
    show('L_save'); bmG.visible = true; cam.position.set(0, 0, 7); cam.lookAt(0, 0, 0);
    const k = seg(t, 0, 0.32); const y = lerp(2.0, -0.25, p3in(k)) + (k >= 1 ? 0.22 * Math.abs(Math.sin((t - 0.32) * 10)) * Math.exp(-(t - 0.32) * 5) : 0);
    bmG.position.set(0, y + 0.2, 0); bmG.scale.setScalar(0.6); bmG.rotation.set(0.12, Math.sin(t * 2.2) * 0.45, 0.04);
    const b = backOut(seg(t, 0.3, 0.6)); css($('#saveChip'), { transform: `translateX(-50%) scale(${b})`, opacity: seg(t, 0.3, 0.38) });
  },
  profile(t, d) {
    show('L_profile'); const a = expoOut(seg(t, 0, 0.4)); css($('#prof'), { transform: `rotateX(${lerp(12, 4, a)}deg) rotateY(${2 - sine(seg(t, 0, d)) * 4}deg) translateY(${(1 - a) * 60}px)`, opacity: a });
    const f = t > 0.8; const btn = $('#fBtn'); btn.textContent = f ? '팔로잉' : '팔로우'; css(btn, { background: f ? 'rgba(255,255,255,.12)' : 'var(--paper)', color: f ? 'var(--paper)' : 'var(--ink)', transform: `scale(${1 - Math.sin(Math.PI * seg(t, 0.55, 0.75)) * 0.05})` });
    fx({ flash: seg(t, d - 0.1, d) * 0.5 });
  },
  dm(t, d) {
    show('L_dm'); const a = expoOut(seg(t, 0, 0.4)); css($('#cmt'), { transform: `rotateX(${lerp(14, 5, a)}deg) translateY(${(1 - a) * 60}px)`, opacity: a });
    const word = '끄기'; const n = Math.floor(seg(t, 0.25, 0.6) * (word.length + 0.99)); $('#typed').textContent = word.slice(0, n); $('#caret').style.opacity = Math.floor(t * 4) % 2 ? 0.2 : 1;
    const b = expoOut(seg(t, 0.8, 1.3)); css($('#dm'), { transform: `perspective(1400px) rotateY(${lerp(-70, -6, b)}deg) translateX(${(1 - b) * 300}px)`, opacity: b });
    fx({ flashIn: 1 - seg(t, 0, 0.12) });
  },
};

function render(t) {
  const s = SC.find((x) => t >= x.t0 && t < x.t1) || SC[SC.length - 1];
  const lt = t - s.t0, d = s.t1 - s.t0;
  $('#stage').className = 'stage ' + (s.lay === 'split' ? 'split' : s.lay === 'host' ? 'hostonly' : '');
  $('#seam').style.display = s.lay === 'split' ? 'block' : 'none';
  const host = $('#host'); if (PREVIEW) { host.style.display = s.lay === 'full' ? 'none' : 'block'; css(host, s.lay === 'split' ? { top: '960px', height: '960px' } : { top: '0px', height: '1920px' }); }
  [bitG, adG, bmG].forEach((g) => (g.visible = false));
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
