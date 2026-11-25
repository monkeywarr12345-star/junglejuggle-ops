import * as THREE from 'three';
import { RoomEnvironment } from './vendor/RoomEnvironment.js';
import { RoundedBoxGeometry } from './vendor/RoundedBoxGeometry.js';
const $ = (s) => document.querySelector(s);
const cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const seg = (t, a, b) => cl((t - a) / (b - a));
const eo = (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
const bo = (x, s = 2.2) => 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2);
const sine = (x) => -(Math.cos(Math.PI * x) - 1) / 2;
const lerp = (a, b, x) => a + (b - a) * x;
const css = (el, o) => Object.assign(el.style, o);

const T = await fetch('tl.json').then((r) => r.json());
const EV = T.ev || {};
await document.fonts.load('900 40px P'); await document.fonts.load('800 40px P'); await document.fonts.load('700 40px P');

// preload images
const cache = {};
function img(src) { if (!cache[src]) { const i = new Image(); i.src = src; cache[src] = i; } return cache[src]; }
const MEME = { m1b_sunglass: 198, m2_point: 56, m1_mindblown: 426, m3_wolf: 48, m3b_wolfclap: 96, m5_popcorn: 46 };
async function preload() { const ps = []; for (let i = 1; i <= 829; i++) ps.push(img(`fx/c${String(i).padStart(4, '0')}.jpg`).decode().catch(() => {})); for (const [k, n] of Object.entries(MEME)) for (let i = 1; i <= n; i++) ps.push(img(`m/${k}/f${String(i).padStart(4, '0')}.jpg`).decode().catch(() => {})); await Promise.all(ps); }
await preload();

// ---------- three: app icon + dust ----------
const R = new THREE.WebGLRenderer({ canvas: $('#gl'), antialias: true, alpha: true, preserveDrawingBuffer: true });
R.setPixelRatio(1); R.setSize(1080, 1920, false); R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 0.9; R.outputColorSpace = THREE.SRGBColorSpace;
const scene = new THREE.Scene(); scene.environment = new THREE.PMREMGenerator(R).fromScene(new RoomEnvironment(), 0.04).texture;
const cam = new THREE.PerspectiveCamera(35, 1080 / 1920, 0.1, 100); cam.position.set(0, 0, 10);
scene.add(new THREE.DirectionalLight(0xffffff, 1.6).translateX(-3).translateY(5).translateZ(5));
const rim = new THREE.PointLight(0x8fa6ff, 50, 30, 1.6); rim.position.set(0, 1, -4); scene.add(rim);
function ctex(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; }
// app icon: earth app icon from footage-like look (generic globe)
const iconTex = ctex(512, 512, (g) => { const gr = g.createRadialGradient(220, 200, 20, 256, 256, 300); gr.addColorStop(0, '#5aa0ff'); gr.addColorStop(0.5, '#1d3f9e'); gr.addColorStop(1, '#050a1c'); g.fillStyle = '#0b0e18'; g.fillRect(0, 0, 512, 512); g.fillStyle = gr; g.beginPath(); g.arc(256, 256, 170, 0, 7); g.fill(); g.fillStyle = 'rgba(120,200,140,.75)'; for (let i = 0; i < 9; i++) { g.beginPath(); g.ellipse(180 + (i * 37) % 160, 190 + (i * 53) % 150, 30 + (i % 3) * 12, 18, i, 0, 7); g.fill(); } g.strokeStyle = 'rgba(255,255,255,.5)'; g.lineWidth = 3; g.beginPath(); g.ellipse(256, 256, 230, 70, -0.4, 0, 7); g.stroke(); });
const icon = new THREE.Mesh(new RoundedBoxGeometry(2.2, 2.2, 0.35, 6, 0.42), [0, 1, 2, 3].map(() => new THREE.MeshPhysicalMaterial({ color: 0x0b0e18, roughness: 0.2, clearcoat: 1 })).concat([new THREE.MeshPhysicalMaterial({ map: iconTex, roughness: 0.25, clearcoat: 1 }), new THREE.MeshPhysicalMaterial({ color: 0x0b0e18 })]));
icon.visible = false; scene.add(icon);
const dg = new THREE.BufferGeometry(); { const n = 220, p = new Float32Array(n * 3); for (let i = 0; i < n; i++) { p[i * 3] = (Math.random() - 0.5) * 12; p[i * 3 + 1] = (Math.random() - 0.5) * 20; p[i * 3 + 2] = -6 + Math.random() * 8; } dg.setAttribute('position', new THREE.BufferAttribute(p, 3)); }
const dust = new THREE.Points(dg, new THREE.PointsMaterial({ size: 0.05, color: 0xcfd8ff, transparent: true, opacity: 0.4, depthWrite: false, blending: THREE.AdditiveBlending })); scene.add(dust);

// ---------- helpers ----------
const layers = [...document.querySelectorAll('.L')];
const show = (id) => layers.forEach((l) => (l.style.visibility = l.id === id ? 'visible' : 'hidden'));
const fimg = $('#fimg'), win = $('#win'), ring = $('#ring');
function footage(t, sc) { const s = sc.fs + (t) * (sc.r || 1); const i = cl(Math.round(s * 30) + 1, 1, 829); fimg.src = `fx/c${String(i).padStart(4, '0')}.jpg`; }
function zoomTo(a, b, x) { const z = (r) => 1600 / r[2]; const r = [lerp(a[0], b[0], x), lerp(a[1], b[1], x), lerp(a[2], b[2], x)]; const k = z(r); fimg.style.transform = `scale(${k}) translate(${-r[0] * 0.625}px,${-r[1] * 0.625}px)`; return r; }
function ringAt(src, cur, on) { if (!on) { ring.style.display = 'none'; return; } const k = 1600 / cur[2]; const x = (src[0] - cur[0]) * 0.625 * k, y = (src[1] - cur[1]) * 0.625 * k, w = src[2] * 0.625 * k, h = src[3] * 0.625 * k; css(ring, { display: 'block', left: x - 8 + 'px', top: y - 8 + 'px', width: w + 16 + 'px', height: h + 16 + 'px', opacity: on }); }
function chip(el, txt, t0, t) { if (!txt) { el.style.display = 'none'; return; } el.style.display = 'inline-flex'; el.textContent = txt; const k = bo(seg(t, t0, t0 + 0.35)); css(el, { transform: `translateX(-50%) scale(${k})`, opacity: seg(t, t0, t0 + 0.08) }); }
function winIn(t, d) { const a = eo(seg(t, 0, 0.45)); css(win, { transform: `translateY(${(1 - a) * 120}px) rotateX(${lerp(16, 4, a) + Math.sin(t * 0.8) * 1.2}deg) rotateY(${-3 + sine(seg(t, 0, d)) * 6}deg) scale(${lerp(0.9, 1, a)})`, opacity: a }); }
function titles(k, tt, t) { $('#kick').innerHTML = k || ''; $('#title').innerHTML = tt || ''; const a = eo(seg(t, 0.05, 0.45)); css($('#title'), { opacity: a, transform: `translateY(${(1 - a) * 30}px)` }); css($('#kick'), { opacity: a }); }
function meme(t, d, name, top) { show('L_meme'); const n = MEME[name]; const i = cl(Math.floor(t * 30) % n + 1, 1, n); $('#mimg').src = `m/${name}/f${String(i).padStart(4, '0')}.jpg`; $('#memeTop').innerHTML = top || ''; const a = bo(seg(t, 0, 0.25), 1.6); css($('#meme'), { transform: `rotate(${lerp(-6, -2, a)}deg) scale(${lerp(0.6, 1, a)})`, opacity: seg(t, 0, 0.06) }); css($('#memeTop'), { transform: `scale(${bo(seg(t, 0.08, 0.35))})` }); }

// ---------- scenes ----------
const U = {
  hook(t, d, S) { show('L_win'); footage(t, S); titles('클로드한테 말로만 했는데', '내 컴퓨터에<br><em>앱이 깔렸어요</em>', t + 1); winIn(t + 1, d + 1); zoomTo([0, 0, 1600], [0, 0, 1500], seg(t, 0, d)); ringAt(0, 0, 0); chip($('#chipA'), '코딩 0줄 · 버튼 1개', -1, t); chip($('#chipB'), '', 0, t); },
  m_wow(t, d) { meme(t, d, 'm1b_sunglass', '진짜로요?'); },
  prompt(t, d, S) { show('L_win'); footage(t, S); titles('이렇게 말만 하면', '"이런 앱 하나<br><em>만들어 줘"</em>', t); winIn(t, d); const c = zoomTo([0, 0, 1600], [140, 40, 700], sine(seg(t, 0.2, 1.4))); ringAt([190, 72, 500, 95], c, seg(t, 1.2, 1.5)); chip($('#chipA'), '우주 쓰레기 추적 앱 만들어 줘', 1.3, t); chip($('#chipB'), '', 0, t); },
  menu(t, d, S) { show('L_win'); footage(t, S); titles('어제부터 생긴 버튼', '<em>앱으로 설치</em>', t); winIn(t, d); const c = zoomTo([200, 100, 1300], [380, 300, 700], sine(seg(t, 0.3, 1.6))); ringAt([470, 388, 330, 40], c, seg(t, 1.2, 1.4)); chip($('#chipA'), 'Install as app', 1.4, t); chip($('#chipB'), '클로드 데스크톱 앱 (맥·윈도우)', 1.9, t); },
  install(t, d, S) { show('L_win'); footage(t, S); titles('딱 누르면', '아이콘 생기고<br><em>창이 따로 떠요</em>', t); winIn(t, d); const ft = S.fs + t * (S.r || 1); const c = ft < 6.2 ? zoomTo([400, 300, 1100], [700, 380, 800], sine(seg(t, 0, 1))) : zoomTo([0, 0, 1600], [0, 0, 1600], 1); ringAt([1090, 520, 130, 60], c, ft < 6 ? seg(t, 0.4, 0.6) : 0); chip($('#chipA'), ft > 6.4 && t < d - 1.4 ? '바탕화면에 아이콘' : '', 0, t); chip($('#chipB'), '', 0, t);
    icon.visible = t > d - 1.4; const k = eo(seg(t, d - 1.4, d - 0.7)); icon.scale.setScalar(0.42); icon.position.set(lerp(2.0, 0.72, k), lerp(-1.6, -0.55, k), lerp(-2, 2.6, k)); icon.rotation.set(0.25 - k * 0.2, -0.6 + k * 0.6 + Math.sin(t * 2) * 0.08, 0); },
  m_point(t, d) { meme(t, d, 'm2_point', '그냥 진짜 프로그램'); },
  perms(t, d, S) { show('L_win'); footage(t, S); titles('허락하면', '알림 · 메뉴 막대 ·<br><em>내 파일까지</em>', t); winIn(t, d); zoomTo([0, 0, 1600], [100, 60, 1400], seg(t, 0, d)); ringAt(0, 0, 0); chip($('#chipA'), '🔔 알림 · 메뉴 막대', 0.8, t); chip($('#chipB'), '📁 내 파일 (허락할 때만)', 1.6, t); },
  update(t, d, S) { show('L_win'); footage(t, S); titles('고치고 싶으면', '"여기 바꿔 줘"<br>→ <em>자동 업데이트</em>', t); winIn(t, d); zoomTo([0, 0, 1600], [80, 40, 1450], seg(t, 0, d)); ringAt(0, 0, 0); chip($('#chipA'), '깔린 앱이 알아서 업데이트', 1.0, t); chip($('#chipB'), '', 0, t); },
  m_blown(t, d) { meme(t, d, 'm1_mindblown', '개발자들 지금'); },
  nogate(t, d, S) { show('L_stamp'); const T0 = S.t0 + t; ['#r0', '#r1', '#r2'].forEach((q, i) => { const t0 = EV['r' + i] - 0.1; const a = eo(seg(T0, t0, t0 + 0.4)); css($(q), { transform: `translateX(${(1 - a) * -200}px) rotateY(${(1 - a) * 30}deg)`, opacity: a }); const st = eo(seg(T0, t0 + 0.35, t0 + 0.6)); css($(q).querySelector('.strike'), { width: st * 62 + '%' }); css($(q).querySelector('.x'), { transform: `scale(${bo(seg(T0, t0 + 0.4, t0 + 0.7))})` }); }); const fc = $('#freeChip'); const k = bo(seg(T0, EV.free - 0.05, EV.free + 0.3)); css(fc, { transform: `translateX(-50%) scale(${k})`, opacity: seg(T0, EV.free - 0.05, EV.free + 0.05) }); },
  m_wolf(t, d) { meme(t, d, 'm3_wolf', '앱스토어 심사 대기?<br>그게 뭔데'); },
  warn(t, d, S) { show('L_warn'); const T0 = S.t0 + t; ['#w0', '#w1', '#w2'].forEach((q, i) => { const t0 = EV['w' + i] - 0.15; const a = eo(seg(T0, t0, t0 + 0.4)); css($(q), { transform: `translateY(${(1 - a) * 60}px)`, opacity: a }); }); $('#gauge').style.width = lerp(90, 20, seg(T0, EV.w1, EV.w1 + 1.6)) + '%'; },
  vs(t, d, S) { show('L_vs'); const T0 = S.t0 + t; const a = eo(seg(t, 0, 0.4)), b = eo(seg(T0, EV.vsB - 0.15, EV.vsB + 0.25)); css($('#vsA'), { transform: `translateX(${(1 - a) * -300}px) rotateY(${12 - a * 6}deg)` }); css($('#vsB'), { transform: `translateX(${(1 - b) * 300}px) rotateY(${-12 + b * 6}deg)` }); css($('#vsMid'), { transform: `translate(-50%,-50%) scale(${bo(seg(T0, EV.vsB + 0.1, EV.vsB + 0.4))})` }); css($('#vsB'), { opacity: b }); },
  m_pop(t, d) { meme(t, d, 'm5_popcorn', '댓글창 구경 중'); },
  cta(t, d, S) { show('L_cta'); const T0 = S.t0 + t; const w = '앱'; $('#typed').textContent = T0 > EV.type ? w : ''; $('#caret').style.opacity = Math.floor(t * 4) % 2 ? 0.2 : 1; const b = eo(seg(T0, EV.dm, EV.dm + 0.5)); css($('#dm'), { transform: `perspective(1400px) rotateY(${lerp(-60, -4, b)}deg) translateX(${(1 - b) * 300}px)`, opacity: b }); css($('#cbox'), { opacity: eo(seg(t, 0, 0.3)) }); },
};
function flash(v) { $('#flash').style.opacity = v || 0; }

// ---------- captions ----------
let lastCap = -1;
function captions(t) {
  let i = -1; for (let k = 0; k < T.caps.length; k++) if (t >= T.caps[k][0]) i = k; const c = T.caps[i]; const el = $('#cap'); if (!c) { el.innerHTML = ''; return; }
  if (i !== lastCap) { el.innerHTML = `<div class="l1">${c[1]}</div>${c[2] ? `<div class="l2">${c[2]}</div>` : ''}`; lastCap = i; }
  const lt = t - c[0]; const a = eo(seg(lt, 0, 0.3)); css(el.querySelector('.l1'), { opacity: a, transform: `translateY(${(1 - a) * 12}px)` });
  const l2 = el.querySelector('.l2'); if (l2) { const s = c[3] != null ? c[3] - c[0] - 0.06 : 0.15; const b = eo(seg(lt, s, s + 0.33)); css(l2, { opacity: b, transform: `translateY(${(1 - b) * 12}px) scale(${lerp(0.95, 1, b)})` }); }
}

function render(t) {
  const S = T.scenes.find((s) => t >= s.t0 && t < s.t1) || T.scenes[T.scenes.length - 1];
  const lt = t - S.t0, d = S.t1 - S.t0;
  document.documentElement.style.setProperty('--hue', S.hue || '#1A1C22');
  icon.visible = false; flash(0);
  U[S.id] && U[S.id](lt, d, S);
  // global transition flash on scene start
  if (t > 0.2) flash(Math.max(parseFloat($('#flash').style.opacity) || 0, (1 - seg(lt, 0, 0.08)) * (S.id.startsWith('m_') ? 0.5 : 0.25)));
  dust.rotation.y = t * 0.03; R.render(scene, cam);
  $('#turb').setAttribute('seed', String(Math.floor(t * 30) % 97));
  $('#credit').textContent = S.credit || '';
  captions(t);
}
window.__timelines = { main: { seek: async (t) => { render(t); await Promise.all([fimg.decode().catch(()=>{}), $('#mimg').decode().catch(()=>{})]); }, duration: () => T.dur } };
window.__ready = true; render(0);
