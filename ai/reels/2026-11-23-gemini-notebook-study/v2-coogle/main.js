import * as THREE from 'three';
import { RoomEnvironment } from './vendor/RoomEnvironment.js';
import { RoundedBoxGeometry } from './vendor/RoundedBoxGeometry.js';

const Q = new URLSearchParams(location.search);
const PREVIEW = Q.has('preview');
const $ = (s) => document.querySelector(s);

// ---------- easing ----------
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

// ---------- timeline (placeholder times; retimed from the voice file) ----------
const TL = await fetch('tl.json').then((r) => r.json()).catch(() => null);
const DEF = {
  dur: 30.4,
  scenes: [
    ['hook', 0, 2.8, 'split', '#3B0A16'],
    ['burst', 2.8, 5.6, 'full', '#0A2163'],
    ['rename', 5.6, 8.4, 'split', '#14203F'],
    ['zero', 8.4, 10.4, 'full', '#04402F'],
    ['src', 10.4, 12.4, 'split', '#0A2163'],
    ['fifty', 12.4, 14.2, 'full', '#0A2163'],
    ['quizArch', 14.2, 15.8, 'full', '#2B1670'],
    ['quiz', 15.8, 17.0, 'split', '#2B1670'],
    ['cite', 17.0, 19.6, 'split', '#2B1670'],
    ['flash', 19.6, 22.0, 'full', '#4B0F42'],
    ['audio', 22.0, 24.0, 'split', '#4B0F42'],
    ['host', 24.0, 25.2, 'host', '#1A1C22'],
    ['save', 25.2, 26.6, 'split', '#1A1C22'],
    ['profile', 26.6, 28.2, 'split', '#1A1C22'],
    ['dm', 28.2, 30.4, 'full', '#1A1C22'],
  ],
  caps: [
    [0.0, '시험공부, 요약 노트', '이제 안 만들어도 돼요'],
    [2.8, '강의 PDF 하나 넣으면', '퀴즈가 쏟아지거든요'],
    [5.6, '구글 제미나이 노트북이에요', '옛 이름은 노트북LM'],
    [8.4, '구글 계정만 있으면', '0원이에요'],
    [10.4, '첫 번째, 자료 넣기', ''],
    [11.4, 'PDF랑 유튜브 링크까지', ''],
    [12.4, '한 번에', '50개 돼요'],
    [14.2, '두 번째, 퀴즈 버튼', ''],
    [15.8, '내 자료로만', '문제를 내 줘요'],
    [17.0, '틀린 건 물어보면', '근거를 짚어서 답해요'],
    [19.6, '세 번째, 플래시카드', ''],
    [20.8, '저는 이걸로 외우고', ''],
    [22.0, '출근길엔', '오디오로 들어요'],
    [24.0, '시험 전날 꺼내 봐요', ''],
    [25.2, '저장해 두세요', ''],
    [26.6, "댓글에 '공부' 남기면", ''],
    [28.2, '공부 프롬프트', 'DM 드려요'],
  ],
};
const T = Object.assign({}, DEF, TL || {});
const EV = Object.assign({ strike: 0.9, zeroSlam: 1.0, scramble: 1.2, dmArrive: 1.2, typing: 0.4 }, T.ev || {});
const SC = T.scenes.map(([id, t0, t1, lay, hue]) => ({ id, t0, t1, lay, hue }));

await document.fonts.load('800 40px P'); await document.fonts.load('700 40px P'); await document.fonts.load('600 40px P'); await document.fonts.load('900 40px P');

// ---------- three setup ----------
const canvas = $('#gl');
const R = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
R.setPixelRatio(1); R.setSize(1080, 1920, false);
R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 0.78; R.outputColorSpace = THREE.SRGBColorSpace;
const pmrem = new THREE.PMREMGenerator(R);
const envTex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
const scene = new THREE.Scene(); scene.environment = envTex;
const cam = new THREE.PerspectiveCamera(35, 1080 / 1920, 0.1, 200);
const key = new THREE.DirectionalLight(0xffffff, 1.3); key.position.set(-4, 6, 6); scene.add(key);
const rim = new THREE.PointLight(0x8fa6ff, 60, 30, 1.6); rim.position.set(0, 2, -5); scene.add(rim);
const rim2 = new THREE.PointLight(0x5b6cff, 40, 30, 1.6); rim2.position.set(4, -2, -4); scene.add(rim2);
const fill = new THREE.PointLight(0xffb27a, 12, 30, 2); fill.position.set(5, -1, 6); scene.add(fill);
scene.add(new THREE.AmbientLight(0xffffff, 0.05)); scene.fog = new THREE.FogExp2(0x07080a, 0.05);

function ctex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); draw(g, w, h); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; }
const rr = (g, x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };

// paper (handwritten summary note)
function paperTex(seed) {
  const r = rng(seed);
  return ctex(512, 700, (g, w, h) => {
    g.fillStyle = '#f2eee4'; g.fillRect(0, 0, w, h);
    g.strokeStyle = 'rgba(80,120,200,.25)'; g.lineWidth = 2;
    for (let y = 90; y < h; y += 38) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
    g.strokeStyle = 'rgba(220,80,80,.35)'; g.beginPath(); g.moveTo(60, 0); g.lineTo(60, h); g.stroke();
    g.font = '700 30px P'; g.fillStyle = '#1d2a55'; g.fillText(['요약 노트', '중간고사 정리', '3주차 핵심', '암기 리스트'][seed % 4], 76, 62);
    for (let y = 120; y < h - 20; y += 38) {
      const len = 160 + r() * 300; g.strokeStyle = r() < 0.2 ? '#b23b3b' : '#2a2f40'; g.lineWidth = 2.6; g.beginPath(); g.moveTo(76, y - 10);
      for (let x = 76; x < 76 + len; x += 8) g.lineTo(x, y - 10 + Math.sin(x * 0.35 + r() * 6) * 5 * r());
      g.stroke();
      if (r() < 0.25) { g.fillStyle = 'rgba(255,230,60,.45)'; g.fillRect(70, y - 26, len * 0.7, 26); }
    }
    g.strokeStyle = 'rgba(200,40,40,.7)'; g.lineWidth = 4; g.beginPath(); g.ellipse(300 + r() * 80, 300 + r() * 200, 80, 34, -0.1, 0, 7); g.stroke();
  });
}
function pdfTex() {
  return ctex(512, 700, (g, w, h) => {
    g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#e5493a'; rr(g, 36, 36, 96, 48, 10); g.fill(); g.fillStyle = '#fff'; g.font = '800 26px P'; g.fillText('PDF', 56, 70);
    g.fillStyle = '#20232b'; g.font = '800 34px P'; g.fillText('3주차 강의안', 36, 140); g.font = '600 22px P'; g.fillStyle = '#8a8f9c'; g.fillText('경영학원론 · 마케팅 믹스', 36, 176);
    for (let y = 220; y < h - 40; y += 30) { g.fillStyle = y % 150 < 30 ? '#c9ccd6' : '#dfe1e8'; g.fillRect(36, y, 300 + ((y * 37) % 140), 12); }
  });
}
function quizTex(i) {
  return ctex(600, 760, (g, w, h) => {
    const grd = g.createLinearGradient(0, 0, w, h); grd.addColorStop(0, '#1d2030'); grd.addColorStop(1, '#0e0f15'); g.fillStyle = grd; g.fillRect(0, 0, w, h);
    g.strokeStyle = 'rgba(143,166,255,.55)'; g.lineWidth = 4; rr(g, 4, 4, w - 8, h - 8, 34); g.stroke();
    g.fillStyle = '#8FA6FF'; rr(g, 40, 40, 120, 54, 27); g.fill(); g.fillStyle = '#07080A'; g.font = '800 30px P'; g.fillText('Q' + (i + 1), 70, 78);
    g.fillStyle = '#F5F5F7'; g.font = '800 38px P';
    const qs = ['침투 가격의 목적은?', '4P에 해당하지 않는 것은?', 'STP의 T는?', '스키밍 가격이란?', '브랜드 자산 구성요소는?', '포지셔닝 맵의 축은?', '시장 세분화 기준은?', '제품 수명주기 3단계는?', 'PPL의 뜻은?', 'USP란?', '가격 탄력성이 큰 상품은?', '푸시 전략이란?'];
    g.fillText(qs[i % qs.length], 40, 160);
    ['A', 'B', 'C', 'D'].forEach((k, j) => { const y = 230 + j * 118; const ok = j === 1 && i % 3 === 0; g.fillStyle = ok ? 'rgba(143,166,255,.22)' : 'rgba(255,255,255,.05)'; rr(g, 40, y, w - 80, 92, 18); g.fill(); g.strokeStyle = ok ? '#8FA6FF' : 'rgba(255,255,255,.16)'; g.lineWidth = 3; g.stroke(); g.fillStyle = ok ? '#8FA6FF' : '#9CA0AB'; g.font = '800 28px P'; g.fillText(k, 72, y + 58); g.fillStyle = 'rgba(255,255,255,.28)'; g.fillRect(120, y + 38, 180 + ((i + j) * 53) % 200, 16); });
  });
}
function slabTex() {
  return ctex(768, 1024, (g, w, h) => {
    const grd = g.createLinearGradient(0, 0, w, h); grd.addColorStop(0, '#11141d'); grd.addColorStop(1, '#090a0f'); g.fillStyle = grd; g.fillRect(0, 0, w, h);
    g.strokeStyle = 'rgba(143,166,255,.10)'; g.lineWidth = 1; for (let x = 0; x < w; x += 48) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); } for (let y = 0; y < h; y += 48) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
    const cg = g.createConicGradient(3.5, 120, 140); cg.addColorStop(0, '#4c7dff'); cg.addColorStop(0.4, '#8a6bff'); cg.addColorStop(0.7, '#5fa8ff'); cg.addColorStop(1, '#4c7dff');
    g.fillStyle = cg; g.beginPath(); g.arc(120, 140, 44, 0, 7); g.fill(); g.fillStyle = '#0d0f16'; g.beginPath(); g.arc(120, 140, 26, 0, 7); g.fill();
    g.fillStyle = '#F5F5F7'; g.font = '800 64px P'; g.fillText('Gemini', 190, 130); g.fillStyle = '#9CA0AB'; g.font = '700 46px P'; g.fillText('Notebook', 190, 186);
    for (let i = 0; i < 6; i++) { g.fillStyle = 'rgba(255,255,255,.06)'; rr(g, 70, 280 + i * 112, w - 140, 88, 18); g.fill(); g.fillStyle = ['#e5493a', '#ff2d2d', '#4c7dff'][i % 3]; rr(g, 96, 300 + i * 112, 48, 48, 10); g.fill(); g.fillStyle = 'rgba(255,255,255,.35)'; g.fillRect(170, 318 + i * 112, 220 + ((i * 71) % 180), 14); }
  });
}
function iconTex(kind) {
  return ctex(256, 320, (g, w, h) => {
    g.fillStyle = '#fbfbfd'; rr(g, 0, 0, w, h, 28); g.fill();
    const col = { pdf: '#e5493a', yt: '#ff2d2d', doc: '#4c7dff', web: '#2f9d74' }[kind];
    g.fillStyle = col; rr(g, 28, 28, 110, 110, 22); g.fill(); g.fillStyle = '#fff'; g.font = '800 40px P'; g.textAlign = 'center';
    g.fillText({ pdf: 'PDF', yt: '▶', doc: 'Doc', web: 'URL' }[kind], 83, 98); g.textAlign = 'left';
    for (let i = 0; i < 4; i++) { g.fillStyle = '#dfe1e8'; g.fillRect(28, 170 + i * 30, 120 + ((i * 47) % 80), 13); }
  });
}
function flashTex(front) {
  return ctex(640, 860, (g, w, h) => {
    if (front) { const grd = g.createLinearGradient(0, 0, w, h); grd.addColorStop(0, '#1b1d25'); grd.addColorStop(1, '#0d0e13'); g.fillStyle = grd; g.fillRect(0, 0, w, h); g.strokeStyle = 'rgba(143,166,255,.5)'; g.lineWidth = 4; rr(g, 6, 6, w - 12, h - 12, 40); g.stroke();
      g.fillStyle = '#8FA6FF'; g.font = '800 30px P'; g.fillText('질문', 56, 96); g.fillStyle = '#F5F5F7'; g.font = '800 64px P'; g.fillText('침투 가격이란?', 56, 420); g.fillStyle = '#9CA0AB'; g.font = '600 28px P'; g.fillText('탭해서 뒤집기', 56, h - 70);
    } else { g.fillStyle = '#F5F5F7'; g.fillRect(0, 0, w, h); g.fillStyle = '#3a9b6b'; g.font = '800 30px P'; g.fillText('정답', 56, 96); g.fillStyle = '#07080A'; g.font = '800 52px P'; g.fillText('낮은 가격으로', 56, 380); g.fillText('점유율 먼저 확보', 56, 450); g.fillStyle = '#8a8f9c'; g.font = '600 26px P'; g.fillText('출처 · 3주차 강의안 p.14', 56, h - 70); }
  });
}

// ---------- objects ----------
const groups = {};
const G = (id) => (groups[id] = groups[id] || (() => { const g = new THREE.Group(); g.visible = false; scene.add(g); return g; })());
const stdPaper = (map, opts = {}) => new THREE.MeshStandardMaterial({ map, roughness: 0.8, metalness: 0, side: THREE.DoubleSide, envMapIntensity: 0.35, ...opts });

// dust (shared)
const dustG = new THREE.BufferGeometry(); { const r = rng(7); const n = 260; const p = new Float32Array(n * 3); for (let i = 0; i < n; i++) { p[i * 3] = (r() - 0.5) * 16; p[i * 3 + 1] = (r() - 0.5) * 22; p[i * 3 + 2] = -8 + r() * 12; } dustG.setAttribute('position', new THREE.BufferAttribute(p, 3)); }
const dustTex = ctex(64, 64, (g) => { const rg = g.createRadialGradient(32, 32, 0, 32, 32, 32); rg.addColorStop(0, 'rgba(255,255,255,1)'); rg.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = rg; g.fillRect(0, 0, 64, 64); });
const dust = new THREE.Points(dustG, new THREE.PointsMaterial({ size: 0.06, map: dustTex, transparent: true, opacity: 0.45, depthWrite: false, blending: THREE.AdditiveBlending, color: 0xcfd8ff }));
scene.add(dust);

// hook papers
const papers = []; { const r = rng(11); const g = G('papers'); const geo = new THREE.PlaneGeometry(1.5, 2.05); for (let i = 0; i < 26; i++) { const m = new THREE.Mesh(geo, stdPaper(paperTex(i), { envMapIntensity: 0.9, emissive: 0xffffff, emissiveMap: paperTex(i), emissiveIntensity: 0.18 })); const a = r() * Math.PI * 2, rad = 1.2 + r() * 3.4; m.userData = { p: new THREE.Vector3(Math.cos(a) * rad * 1.2, (r() - 0.5) * 5.0, -3.5 - r() * 8), rot: new THREE.Euler((r() - 0.5) * 1.2, (r() - 0.5) * 1.4, (r() - 0.5) * 0.9), v: new THREE.Vector3((r() - 0.5) * 2, (r() - 0.2) * 2, 4 + r() * 6), spin: (r() - 0.5) * 6 }; g.add(m); papers.push(m); } }

// glass notebook slab
const slabG = G('slab');
const slab = new THREE.Mesh(new RoundedBoxGeometry(3.0, 4.0, 0.22, 6, 0.16), new THREE.MeshPhysicalMaterial({ color: 0x0c0e15, roughness: 0.18, metalness: 0.3, clearcoat: 1, clearcoatRoughness: 0.08, envMapIntensity: 1.3 }));
const slabFace = new THREE.Mesh(new THREE.PlaneGeometry(2.78, 3.7), new THREE.MeshStandardMaterial({ map: slabTex(), emissive: 0xffffff, emissiveMap: slabTex(), emissiveIntensity: 0.55, roughness: 0.35 }));
slabFace.position.z = 0.115; slab.add(slabFace);
const halo = new THREE.Mesh(new THREE.PlaneGeometry(6.5, 7.5), new THREE.MeshBasicMaterial({ map: ctex(256, 256, (g) => { const rg = g.createRadialGradient(128, 128, 0, 128, 128, 128); rg.addColorStop(0, 'rgba(143,166,255,.9)'); rg.addColorStop(0.35, 'rgba(91,108,255,.35)'); rg.addColorStop(1, 'rgba(91,108,255,0)'); g.fillStyle = rg; g.fillRect(0, 0, 256, 256); }), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
halo.position.z = -0.6; slabG.add(halo); slabG.add(slab);

// pdf sheet
const pdfM = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 1.9), stdPaper(pdfTex())); G('pdf').add(pdfM);

// quiz cards
const quizCards = []; { const geo = new RoundedBoxGeometry(1.55, 1.96, 0.03, 4, 0.08); const g = G('quiz3d'); for (let i = 0; i < 12; i++) { const mat = [0, 1, 2, 3].map(() => new THREE.MeshStandardMaterial({ color: 0xeceef4, roughness: 0.5 })); const front = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 1.9), new THREE.MeshStandardMaterial({ map: quizTex(i), emissive: 0xffffff, emissiveMap: quizTex(i), emissiveIntensity: 0.35, roughness: 0.4, envMapIntensity: 0.5 })); const c = new THREE.Mesh(geo, new THREE.MeshPhysicalMaterial({ color: 0x151722, roughness: 0.25, metalness: 0.4, clearcoat: 1 })); front.position.z = 0.017; c.add(front); g.add(c); quizCards.push(c); } }

// orbit tiles (50)
const tiles = []; { const r = rng(23); const kinds = ['pdf', 'yt', 'doc', 'web']; const texs = kinds.map(iconTex); const geo = new THREE.PlaneGeometry(0.62, 0.78); const g = G('orbit'); for (let i = 0; i < 50; i++) { const m = new THREE.Mesh(geo, stdPaper(texs[i % 4], { roughness: 0.4 })); m.userData = { a: (i / 50) * Math.PI * 2 + r() * 0.2, rad: 2.6 + r() * 1.2, y: (r() - 0.5) * 1.6, sp: 0.6 + r() * 0.5, tilt: (r() - 0.5) * 0.6 }; g.add(m); tiles.push(m); } }

// flashcard
const flashG = G('flash3d'); const flashCard = new THREE.Group(); { const f = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 3.2), new THREE.MeshStandardMaterial({ map: flashTex(true), roughness: 0.4, metalness: 0.1 })); const b = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 3.2), new THREE.MeshStandardMaterial({ map: flashTex(false), roughness: 0.5 })); b.rotation.y = Math.PI; b.position.z = -0.01; flashCard.add(f, b); flashG.add(flashCard);
  const refl = flashCard.clone(); refl.scale.y = -1; refl.position.y = -3.45; refl.traverse((o) => { if (o.material) { o.material = o.material.clone(); o.material.transparent = true; o.material.opacity = 0.08; } }); flashG.add(refl); flashCard.userData.refl = refl; }

// audio ring
const ringG = G('ring'); const bars = new THREE.InstancedMesh(new THREE.BoxGeometry(0.05, 1, 0.05), new THREE.MeshStandardMaterial({ color: 0x8fa6ff, emissive: 0x5b6cff, emissiveIntensity: 1.6, roughness: 0.3 }), 96); ringG.add(bars);
const ringCore = new THREE.Mesh(new THREE.TorusGeometry(1.25, 0.012, 8, 160), new THREE.MeshBasicMaterial({ color: 0xcfd8ff })); ringG.add(ringCore);

// bookmark (save)
const bmG = G('bookmark'); { const s = new THREE.Shape(); s.moveTo(-0.6, 0.9); s.lineTo(0.6, 0.9); s.lineTo(0.6, -0.9); s.lineTo(0, -0.45); s.lineTo(-0.6, -0.9); s.closePath(); const geo = new THREE.ExtrudeGeometry(s, { depth: 0.25, bevelEnabled: true, bevelThickness: 0.06, bevelSize: 0.05, bevelSegments: 4 }); geo.center(); const m = new THREE.Mesh(geo, new THREE.MeshPhysicalMaterial({ color: 0xf5f5f7, roughness: 0.22, metalness: 0.15, clearcoat: 1, emissive: 0x5b6cff, emissiveIntensity: 0.12 })); bmG.add(m); bmG.userData.m = m; }

// ---------- DOM helpers ----------
const layers = [...document.querySelectorAll('.layer')];
const show = (id) => layers.forEach((l) => (l.style.visibility = l.id === id ? 'visible' : 'hidden'));
const css = (el, o) => Object.assign(el.style, o);
// 0원 extrusion
{ const z = $('#zero'); for (let i = 13; i >= 0; i--) { const d = document.createElement('div'); d.className = 'z'; d.textContent = '0원'; d.style.transform = `translateZ(${-i * 2.2}px)`; d.style.color = i === 0 ? '#F5F5F7' : `color-mix(in srgb,#0B5A43 ${100 - i * 6}%,#07080A)`; if (i === 0) d.style.textShadow = '0 0 80px rgba(120,255,200,.25)'; z.appendChild(d); } }
// source list
{ const L = $('#srcList'); const items = [['PDF', '#e5493a', '3주차 강의안_마케팅.pdf'], ['▶', '#ff2d2d', '유튜브 · 4P 전략 핵심 정리'], ['Doc', '#4c7dff', '조별과제 요약 노트'], ['URL', '#2f9d74', '교수님 블로그 · 가격 전략']]; L.innerHTML = items.map(([k, c, n]) => `<div class="src"><div class="ic" style="background:${c}">${k}</div>${n}<span style="margin-left:auto;color:#3a9b6b;font-weight:800">✓</span></div>`).join(''); }
const srcItems = [...document.querySelectorAll('#srcList .src')];
const turb = $('#turb');
const bloomC = $('#bloom'); const bctx = bloomC.getContext('2d');

// ---------- captions ----------
const capEl = $('#cap');
let lastCap = -1;
function captions(t, lay) {
  let i = -1; for (let k = 0; k < T.caps.length; k++) if (t >= T.caps[k][0]) i = k;
  const c = T.caps[i]; if (!c) { capEl.innerHTML = ''; return; }
  if (i !== lastCap) { capEl.innerHTML = `<div class="l1">${c[1]}</div>${c[2] ? `<div class="l2">${c[2]}</div>` : ''}`; lastCap = i; }
  const lt = t - c[0];
  capEl.style.top = lay === 'split' ? (c[2] ? '842px' : '872px') : '1400px';
  const l1 = capEl.querySelector('.l1'), l2 = capEl.querySelector('.l2');
  const a = expoOut(seg(lt, 0, 0.35)); css(l1, { opacity: a, transform: `translateY(${(1 - a) * 14}px)` });
  if (l2) { const l2t = c[3] != null ? c[3] - c[0] - 0.06 : 0.18; const b = expoOut(seg(lt, l2t, l2t + 0.37)); css(l2, { opacity: b, transform: `translateY(${(1 - b) * 14}px) scale(${lerp(0.96, 1, b)})` }); }
}

// ---------- per-scene updates ----------
function hideAll() { Object.values(groups).forEach((g) => (g.visible = false)); }
const U = {
  hook(t, d) {
    show('L_hook'); const g = groups.papers; g.visible = true;
    cam.position.set(0, 0.2, lerp(9, 6.2, sine(seg(t, 0, d)))); cam.lookAt(0, 0.2, -3);
    const ash = seg(t, 1.9, d);
    papers.forEach((m, i) => { const u = m.userData; const f = p3in(ash); m.position.set(u.p.x + u.v.x * f, u.p.y + Math.sin(t * 0.6 + i) * 0.08 + u.v.y * f, u.p.z + u.v.z * f); m.rotation.set(u.rot.x + t * 0.05 + u.spin * f, u.rot.y + t * 0.07 + u.spin * f, u.rot.z); m.material.opacity = 1 - f; m.material.transparent = f > 0; });
    { const hc = $('#hookChip'); const k = backOut(seg(t, EV.strike + 0.55, EV.strike + 0.9)); css(hc, { transform: `translateX(-50%) scale(${k})`, opacity: seg(t, EV.strike + 0.55, EV.strike + 0.65) * (1 - seg(t, d - 0.25, d)) }); }
    const s = $('#hookT .strike'); s.style.transform = `scaleX(${p4io(seg(t, EV.strike, EV.strike + 0.4))})`;
    const ht = $('#hookT'); const a = expoOut(seg(t, 0, 0.4)); css(ht, { opacity: a * (1 - seg(t, d - 0.25, d)), transform: `translateY(${(1 - a) * 30}px)` });
    { const q = expoOut(seg(t, EV.strike + 0.25, EV.strike + 0.65)); css($('#hookT .b'), { opacity: q, transform: `translateY(${(1 - q) * 20}px)`, display: 'inline-block' }); }
    // slab rising through ash
    if (t > 2.0) { groups.slab.visible = true; const r = expoOut(seg(t, 2.0, d)); groups.slab.position.set(0, lerp(-5, 0.1, r), -1.5); groups.slab.rotation.set(-0.25, 0.35 - r * 0.25, 0); groups.slab.scale.setScalar(0.85); }
    fx({ dip: seg(t, d - 0.13, d) });
  },
  burst(t, d) {
    show('L_none'); groups.slab.visible = true; groups.pdf.visible = true; groups.quiz3d.visible = true;
    cam.position.set(Math.sin(t * 0.4) * 0.6, 1.2, 14 - t * 0.5); cam.lookAt(0, 0.4, 0);
    groups.slab.position.set(0, -1.4, 0); groups.slab.rotation.set(-0.55, 0.25 + t * 0.06, 0); groups.slab.scale.setScalar(0.72);
    const fall = p3in(seg(t, 0, 0.75)); pdfM.position.set(lerp(-0.6, 0, fall), lerp(4.8, -0.4, fall), lerp(1, 0.3, fall)); pdfM.rotation.set(lerp(-0.4, -0.35, fall), lerp(0.6, 0.25, fall), lerp(0.3, 0, fall)); pdfM.scale.setScalar(lerp(1, 0.05, seg(t, 0.62, 0.8))); pdfM.visible = t < 0.8;
    const pulse = Math.exp(-Math.pow((t - 0.8) / 0.18, 2)); slabFace.material.emissiveIntensity = 0.55 + pulse * 2.2; halo.material.opacity = 0.7 + pulse;
    const b = seg(t, 0.85, 2.2);
    quizCards.forEach((c, i) => { const k = expoOut(cl(b * 1.25 - i * 0.04)); const a = -1.15 + (i / 11) * 2.3; const R2 = lerp(0.1, 3.4 + (i % 3) * 0.5, k); c.position.set(Math.sin(a) * R2, -0.4 + lerp(0, 1.8 + Math.cos(a * 2) * 0.8, k), lerp(0, 2.2 + (i % 4) * 1.4, k)); c.rotation.set(-0.2 + (i % 2) * 0.15, -a * 0.6, a * 0.25); c.scale.setScalar(lerp(0.2, 1, k)); c.visible = t > 0.85; });
    // depth push through front card at the end
    const push = p3in(seg(t, d - 0.45, d)); cam.position.z -= push * 6;
    fx({ flash: seg(t, d - 0.12, d) * 0.9, flashIn: 1 - seg(t, 0, 0.1) });
  },
  rename(t, d, S) { const sk = EV.scramble - S.t0;
    show('L_rename'); groups.slab.visible = false;
    const c = $('#gnCard'); const a = expoOut(seg(t, 0, 0.55)); const ex = p3in(seg(t, d - 0.3, d));
    css(c, { transform: `translateY(${(1 - a) * 80}px) rotateX(${lerp(14, 3, a)}deg) rotateY(${-4 + sine(seg(t, 0, d)) * 3 - ex * 70}deg) translateX(${-ex * 500}px)`, opacity: 1 - ex });
    // scramble NotebookLM -> Gemini Notebook
    const s = seg(t, sk, sk + 0.6); const A = 'NotebookLM', B = 'Gemini Notebook'; const n = Math.round(lerp(0, B.length, s)); const ch = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ#$%01'; let out = B.slice(0, n); for (let i = n; i < Math.max(A.length, B.length) && s > 0 && s < 1; i++) out += ch[(i * 7 + Math.floor(t * 30)) % ch.length]; $('#scr').textContent = s <= 0 ? A : s >= 1 ? B : out;
    $('#scr').style.color = s >= 1 ? '#F5F5F7' : '';
    css($('#oldName'), { opacity: expoOut(seg(t, sk - 1.0, sk - 0.6)) * (1 - ex), transform: `scale(${1 + Math.sin(Math.PI * seg(t, sk, sk + 0.6)) * 0.08})` });
  },
  zero(t, d, S) {
    show('L_zero'); const z = $('#zero'); const zs = EV.zeroSlam - S.t0 - 0.08; const a = backOut(seg(t, zs, zs + 0.4));
    css(z, { transform: `translateZ(${lerp(-900, 0, a)}px) rotateY(${lerp(-18, -6, sine(seg(t, 0, d)))}deg) rotateX(6deg) scale(${lerp(1.6, 1, expoOut(seg(t, zs, zs + 0.38)))})`, opacity: seg(t, zs, zs + 0.08) });
    const c = $('#zeroChip'); const b = backOut(seg(t, 0.1, 0.45)); css(c, { transform: `translateX(-50%) translateY(${(1 - expoOut(seg(t, zs, zs + 0.4))) * -380}px) scale(${b})`, opacity: seg(t, 0.1, 0.2) });
    fx({ leak: Math.sin(Math.PI * seg(t, d - 0.25, d)) });
  },
  src(t, d) {
    show('L_src'); const bd = $('#bd1'); const a = expoOut(seg(t, 0, 0.5)); css(bd, { transform: `translateX(${(1 - a) * -60}px)`, opacity: a });
    const c = $('#srcCard'); const b = expoOut(seg(t, 0.1, 0.65)); css(c, { transform: `rotateX(${lerp(12, 4, b)}deg) rotateY(${3 - sine(seg(t, 0, d)) * 5}deg) translateY(${(1 - b) * 60}px) scale(${lerp(0.94, 1, b)})`, opacity: b });
    srcItems.forEach((el, i) => { const k = expoOut(seg(t, 0.55 + i * 0.22, 0.95 + i * 0.22)); css(el, { transform: `translateZ(${(1 - k) * 400}px) translateY(${(1 - k) * -40}px)`, opacity: k }); });
    $('#cnt').textContent = Math.round(lerp(0, 50, p3out(seg(t, 0.6, d - 0.1)))) + ' / 50';
  },
  fifty(t, d) {
    show('L_fifty'); groups.slab.visible = true; groups.orbit.visible = true;
    const k = seg(t, 0, d); cam.position.set(Math.sin(lerp(-0.25, 0.2, sine(k))) * 10.5, lerp(2.6, 1.6, k), Math.cos(lerp(-0.25, 0.2, sine(k))) * 10.5); cam.lookAt(0, 0, 0);
    groups.slab.position.set(0, 0, 0); groups.slab.rotation.set(-0.15, 0, 0); groups.slab.scale.setScalar(0.8); slabFace.material.emissiveIntensity = 0.9; halo.material.opacity = 1;
    tiles.forEach((m, i) => { const u = m.userData; const ent = expoOut(seg(t, i * 0.012, 0.5 + i * 0.012)); const a = u.a + t * u.sp * 0.9; const rad = lerp(9, u.rad, ent); m.position.set(Math.cos(a) * rad, u.y + Math.sin(a * 2) * 0.2, Math.sin(a) * rad * 0.55); m.lookAt(cam.position); m.rotateZ(u.tilt); });
    const c = $('#fiftyChip'); const b = backOut(seg(t, 0.3, 0.7)); css(c, { transform: `translateX(-50%) scale(${b})`, opacity: seg(t, 0.3, 0.4) });
    fx({ whip: seg(t, d - 0.2, d) });
  },
  quizArch(t, d) {
    show('L_quizArch'); groups.quiz3d.visible = true; const bd = $('#bd2'); const a = expoOut(seg(t, 0, 0.45)); css(bd, { transform: `translateX(${(1 - a) * -60}px)`, opacity: a });
    cam.position.set(0, 0.9, lerp(9.0, 8.0, sine(seg(t, 0, d)))); cam.lookAt(0, 0.9, 0);
    const k = expoOut(seg(t, 0.05, 0.8)); const sel = p4io(seg(t, 0.7, 1.3));
    quizCards.forEach((c, i) => { if (i > 6) { c.visible = false; return; } c.visible = true; const a2 = (i - 3) * 0.3 * k; const r = 4.6; c.position.set(Math.sin(a2) * r, 0.9 + (i === 3 ? sel * 0.25 : 0), lerp(-2, Math.cos(a2) * r - r, 1) + (i === 3 ? sel * 2.4 : 0)); c.rotation.set(0, -a2, 0); c.scale.setScalar(0.95); });
    // rack focus: blur canvas except selected (approximate with CSS on canvas)
    canvas.style.filter = `blur(${sel * 0}px)`; bloomC.style.opacity = 0.42 + sel * 0.15;
    fx({ flashIn: 1 - seg(t, 0, 0.15), whipIn: 1 - seg(t, 0, 0.2) });
  },
  quiz(t, d) {
    show('L_quiz'); const c = $('#qCard'); const a = expoOut(seg(t, 0, 0.5)); css(c, { transform: `rotateX(${lerp(10, 3, a)}deg) rotateY(${-3 + sine(seg(t, 0, d)) * 4}deg) scale(${lerp(0.95, 1, a)})`, opacity: a });
    const ok = seg(t, 0.55, 0.7); $('#optB').classList.toggle('ok', ok > 0);
  },
  cite(t, d) {
    show('L_cite'); const c = $('#chatCard'); const a = expoOut(seg(t, 0, 0.5)); css(c, { transform: `rotateY(${lerp(10, 5, a)}deg) rotateX(4deg) translateX(${(1 - a) * -80}px)`, opacity: a });
    const p = $('#pdfCard'); const b = expoOut(seg(t, 0.7, 1.2)); const foc = p4io(seg(t, 1.3, 1.8));
    css(p, { transform: `translateZ(${lerp(-300, -60, b)}px) rotateY(-14deg) rotateX(4deg)`, opacity: b, filter: `blur(${(1 - foc) * 5}px)` });
    css(c, { filter: `blur(${foc * 3}px)` });
    const beam = seg(t, 0.95, 1.45); ['#beamP', '#beamG'].forEach((s) => { const el = $(s); const L = el.getTotalLength(); el.style.strokeDasharray = L; el.style.strokeDashoffset = L * (1 - p3out(beam)); });
    $('#hl').style.background = `rgba(143,166,255,${0.1 + foc * 0.35})`;
  },
  flash(t, d) {
    show('L_flash'); groups.flash3d.visible = true; const bd = $('#bd3'); const a = expoOut(seg(t, 0, 0.45)); css(bd, { transform: `translateX(${(1 - a) * -60}px)`, opacity: a });
    cam.position.set(lerp(-1.2, 1.0, sine(seg(t, 0, d))), 0.4, 8.2); cam.lookAt(0, 0.2, 0);
    const f = p4io(seg(t, 0.9, 1.6)); flashCard.rotation.set(0.05, -0.35 + f * Math.PI + sine(seg(t, 0, d)) * 0.3, 0); flashCard.position.set(0, 0.7 + Math.sin(t * 1.5) * 0.05, 0); flashG.scale.setScalar(0.62);
    const rf = flashCard.userData.refl; rf.rotation.copy(flashCard.rotation); rf.rotation.x = -flashCard.rotation.x;
  },
  audio(t, d) {
    show('L_audio'); groups.ring.visible = true; cam.position.set(0, 0, 7.2); cam.lookAt(0, 0, 0);
    ringG.position.set(0, 0.55, 0); ringG.scale.setScalar(0.72); ringG.rotation.set(-0.35 + Math.sin(t) * 0.05, 0.2 * Math.sin(t * 0.7), 0);
    const st = expoOut(seg(t, 0, 0.6)); const o = new THREE.Object3D();
    for (let i = 0; i < 96; i++) { const a = (i / 96) * Math.PI * 2; const h = (0.15 + 0.75 * Math.abs(Math.sin(i * 0.53 + t * 7) * Math.sin(i * 0.21 - t * 3.1))) * st; o.position.set(Math.cos(a) * (1.35 + h / 2), Math.sin(a) * (1.35 + h / 2), 0); o.rotation.set(0, 0, a - Math.PI / 2); o.scale.set(1, Math.max(0.02, h), 1); o.updateMatrix(); bars.setMatrixAt(i, o.matrix); }
    bars.instanceMatrix.needsUpdate = true;
    const p = $('#player'); const b = expoOut(seg(t, 0.3, 0.8)); css(p, { transform: `translateY(${(1 - b) * 40}px) rotateX(8deg)`, opacity: b }); $('#prog').style.width = lerp(18, 46, seg(t, 0, d)) + '%';
  },
  host() { show('L_none'); },
  save(t, d) {
    show('L_save'); groups.bookmark.visible = true; cam.position.set(0, 0, 7); cam.lookAt(0, 0, 0);
    const k = seg(t, 0, 0.32); const y = lerp(2.0, -0.25, p3in(k)) + (k >= 1 ? 0.22 * Math.abs(Math.sin((t - 0.32) * 10)) * Math.exp(-(t - 0.32) * 5) : 0);
    bmG.position.set(0, y + 0.2, 0); bmG.scale.setScalar(0.6); bmG.rotation.set(0.12, Math.sin(t * 2.2) * 0.45, 0.04);
    const c = $('#saveChip'); const b = backOut(seg(t, 0.3, 0.6)); css(c, { transform: `translateX(-50%) scale(${b})`, opacity: seg(t, 0.3, 0.38) });
  },
  profile(t, d) {
    show('L_profile'); const c = $('#prof'); const a = expoOut(seg(t, 0, 0.5)); css(c, { transform: `rotateX(${lerp(12, 4, a)}deg) rotateY(${2 - sine(seg(t, 0, d)) * 4}deg) translateY(${(1 - a) * 60}px)`, opacity: a });
    const f = seg(t, 0.8, 0.95); const btn = $('#fBtn'); btn.textContent = f > 0 ? '팔로잉' : '팔로우'; css(btn, { background: f > 0 ? 'rgba(255,255,255,.12)' : 'var(--iris4)', transform: `scale(${1 - Math.sin(Math.PI * seg(t, 0.72, 0.95)) * 0.05})` });
    fx({ dip: 0, flash: seg(t, d - 0.1, d) * 0.6 });
  },
  dm(t, d, S) { const ty = EV.typing - S.t0, ar = EV.dmArrive - S.t0;
    show('L_dm'); const c = $('#cmt'); const a = expoOut(seg(t, 0, 0.5)); css(c, { transform: `rotateX(${lerp(14, 5, a)}deg) translateY(${(1 - a) * 60}px)`, opacity: a });
    const word = '공부'; const n = Math.floor(seg(t, ty, ty + 0.45) * (word.length + 0.99)); $('#typed').textContent = word.slice(0, n); $('#caret').style.opacity = Math.floor(t * 4) % 2 ? 0.2 : 1;
    const m = $('#dm'); const b = expoOut(seg(t, ar, ar + 0.55)); css(m, { transform: `perspective(1400px) rotateY(${lerp(-70, -6, b)}deg) translateX(${(1 - b) * 300}px)`, opacity: b });
    fx({ flashIn: 1 - seg(t, 0, 0.12) });
  },
};
function fx(o = {}) {
  $('#flash').style.opacity = Math.max(o.flash || 0, (o.flashIn || 0) * 0.8);
  $('#leak').style.opacity = o.leak || 0;
  $('#dip').style.opacity = o.dip || 0;
  const w = Math.max(o.whip || 0, o.whipIn || 0); $('#dom').style.filter = w > 0.01 ? `blur(${w * 30}px)` : ''; canvas.style.transform = `translateX(${(o.whip || 0) * -260 + (o.whipIn || 0) * 260}px)`; canvas.style.filter = w > 0.01 ? `blur(${w * 36}px)` : '';
}

// ---------- frame ----------
let cur = null;
function render(t) {
  const s = SC.find((x) => t >= x.t0 && t < x.t1) || SC[SC.length - 1];
  const lt = t - s.t0, d = s.t1 - s.t0;
  const st = $('#stage'); st.className = 'stage ' + (s.lay === 'split' ? 'split' : s.lay === 'host' ? 'hostonly' : '');
  document.documentElement.style.setProperty('--hue', s.hue);
  $('#seam').style.display = s.lay === 'split' ? 'block' : 'none';
  const host = $('#host'); if (PREVIEW) { host.style.display = s.lay === 'full' ? 'none' : 'block'; if (s.lay === 'split') css(host, { top: '960px', height: '960px', objectPosition: '50% 12%' }); else css(host, { top: '0px', height: '1920px', objectPosition: '50% 50%' }); }
  hideAll(); slabFace.material.emissiveIntensity = 0.55; halo.material.opacity = 0.8; bloomC.style.opacity = 0.42; canvas.style.filter = ''; canvas.style.transform = ''; $('#dom').style.filter = ''; fx({});
  // camera aspect / viewport
  if (s.lay === 'split') { R.setViewport(0, 960, 1080, 960); R.setScissor(0, 960, 1080, 960); R.setScissorTest(true); cam.aspect = 1080 / 960; } else { R.setViewport(0, 0, 1080, 1920); R.setScissorTest(false); cam.aspect = 1080 / 1920; }
  cam.fov = s.lay === 'split' ? 30 : 35; cam.updateProjectionMatrix();
  dust.position.y = Math.sin(t * 0.2) * 0.3; dust.rotation.y = t * 0.02;
  U[s.id] && U[s.id](lt, d, s);
  R.setClearColor(0x000000, 0); R.clear(); R.render(scene, cam);
  bctx.clearRect(0, 0, 540, 960); bctx.drawImage(canvas, 0, 0, 540, 960);
  turb.setAttribute('seed', String(Math.floor(t * 30) % 97));
  captions(t, s.lay);
  // brand hidden on full-host
  $('#brand').style.opacity = s.lay === 'host' ? 0 : 0.9;
}
const empty = document.createElement('div'); empty.className = 'layer'; empty.id = 'L_none'; $('#dom').appendChild(empty); layers.push(empty);
window.__timelines = { main: { seek: (t) => render(t), duration: () => T.dur } };
window.__T = T; window.__ready = true;
render(Number(Q.get('t') || 0));
