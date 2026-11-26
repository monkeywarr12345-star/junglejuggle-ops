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
const IMGS = ['src/gh_tells.jpg','src/gh_header.jpg','src/gh_readme.jpg','src/gh_code.jpg','src/cl_plugins.jpg','src/cl_upload.jpg'];
async function preload() { const ps = IMGS.map((u) => img(u).decode().catch(() => {})); for (const [k, n] of Object.entries(MEME)) for (let i = 1; i <= n; i++) ps.push(img(`m/${k}/f${String(i).padStart(4, '0')}.jpg`).decode().catch(() => {})); await Promise.all(ps); }
await preload();

// ---------- three: app icon + dust ----------
const R = new THREE.WebGLRenderer({ canvas: $('#gl'), antialias: true, alpha: true, preserveDrawingBuffer: true });
R.setPixelRatio(1); R.setSize(1080, 1920, false); R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 0.9; R.outputColorSpace = THREE.SRGBColorSpace;
const scene = new THREE.Scene(); scene.environment = new THREE.PMREMGenerator(R).fromScene(new RoomEnvironment(), 0.04).texture;
const cam = new THREE.PerspectiveCamera(35, 1080 / 1920, 0.1, 100); cam.position.set(0, 0, 10);
scene.add(new THREE.DirectionalLight(0xffffff, 1.6).translateX(-3).translateY(5).translateZ(5));
const rim = new THREE.PointLight(0xa99bff, 50, 30, 1.6); rim.position.set(0, 1, -4); scene.add(rim);
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
function footage(t, sc, src) { const u = src || sc.img; if (!fimg.src.endsWith(u)) fimg.src = u; const bar = win.querySelector('.bar'); if (bar) bar.textContent = ''; }
function zoomTo(a, b, x) { const z = (r) => 1600 / r[2]; const r = [lerp(a[0], b[0], x), lerp(a[1], b[1], x), lerp(a[2], b[2], x)]; const k = z(r); fimg.style.transform = `scale(${k}) translate(${-r[0] * 0.625}px,${-r[1] * 0.625}px)`; return r; }
function ringAt(src, cur, on) { if (!on) { ring.style.display = 'none'; return; } const k = 1600 / cur[2]; const x = (src[0] - cur[0]) * 0.625 * k, y = (src[1] - cur[1]) * 0.625 * k, w = src[2] * 0.625 * k, h = src[3] * 0.625 * k; css(ring, { display: 'block', left: x - 8 + 'px', top: y - 8 + 'px', width: w + 16 + 'px', height: h + 16 + 'px', opacity: on }); }
function chip(el, txt, t0, t) { if (!txt) { el.style.display = 'none'; return; } el.style.display = 'inline-flex'; el.textContent = txt; const k = bo(seg(t, t0, t0 + 0.35)); css(el, { transform: `translateX(-50%) scale(${k})`, opacity: seg(t, t0, t0 + 0.08) }); }
function winIn(t, d, S) { if (S && S.cont) { const a = eo(seg(t, 0, 0.5)); css(win, { transform: `rotateX(${4 + Math.sin(t * 0.8) * 1.2}deg) rotateY(${-3 + sine(seg(t, 0, d)) * 6}deg) scale(${lerp(1.05, 1, a)})`, opacity: 1 }); return; } const a = eo(seg(t, 0, 0.45)); css(win, { transform: `translateY(${(1 - a) * 120}px) rotateX(${lerp(16, 4, a) + Math.sin(t * 0.8) * 1.2}deg) rotateY(${-3 + sine(seg(t, 0, d)) * 6}deg) scale(${lerp(0.9, 1, a)})`, opacity: a }); }
function titles(k, tt, t) { $('#kick').innerHTML = k || ''; $('#title').innerHTML = tt || ''; const a = eo(seg(t, 0.05, 0.45)); css($('#title'), { opacity: a, transform: `translateY(${(1 - a) * 30}px)` }); css($('#kick'), { opacity: a }); }
function meme(t, d, name, top) { show('L_meme'); const n = MEME[name]; const i = cl(Math.floor(t * 30) % n + 1, 1, n); $('#mimg').src = `m/${name}/f${String(i).padStart(4, '0')}.jpg`; $('#memeTop').innerHTML = top || ''; const a = bo(seg(t, 0, 0.25), 1.6); css($('#meme'), { transform: `rotate(${lerp(-6, -2, a)}deg) scale(${lerp(0.6, 1, a)})`, opacity: seg(t, 0, 0.06) }); css($('#memeTop'), { transform: `scale(${bo(seg(t, 0.08, 0.35))})` }); }

// ---------- scenes ----------
const U = {
  hook(t, d, S) { show('L_hook'); const a = eo(seg(t + 0.6, 0, 0.5)); css($('#hkA'), { opacity: a, transform: `translateY(${(1 - a) * 30}px)` }); const b = bo(seg(t, 0.25, 0.6), 1.4); css($('#hkB'), { opacity: seg(t, 0.25, 0.32), transform: `scale(${lerp(0.7, 1, b)})` }); chip($('#hkChip'), 'AI 티 26개 · 0원', 0.55, t); },
  m_point(t, d) { meme(t, d, 'm2_point', '이거 <em>AI</em>가 썼네?'); },
  tells(t, d, S) { show('L_win'); footage(t, S); titles('근데 그 티를', '<em>26개</em> 찾아서<br>지워 줘요', t); winIn(t, d, S); zoomTo([40, 260, 1150], [100, 400, 760], sine(seg(t, 0.3, d))); ringAt(0, 0, 0); chip($('#chipA'), '"Let that sink in." 같은 말투', 1.0, t); chip($('#chipB'), '총 26개 패턴 체크', 2.2, t); },
  name(t, d, S) { show('L_win'); footage(t, S); titles('이름은', '<em>휴머나이저</em>', t); winIn(t, d, S); zoomTo([0, 0, 1600], [40, 110, 700], sine(seg(t, 0, d))); ringAt(0, 0, 0); chip($('#chipA'), 'Humanizer · 클로드 스킬', 0.5, t); chip($('#chipB'), '', 0, t); },
  wiki(t, d, S) { show('L_win'); footage(t, S); titles('기준은', '위키백과<br><em>AI 글 판별법</em>', t); winIn(t, d, S); zoomTo([60, 120, 1150], [100, 160, 820], sine(seg(t, 0.4, d))); ringAt(0, 0, 0); chip($('#chipA'), 'Wikipedia: Signs of AI writing', 1.2, t); chip($('#chipB'), '편집자들이 AI 글 잡을 때 쓰는 가이드', 2.4, t); },
  stars(t, d, S) { show('L_win'); footage(t, S); titles('깃허브 별', '<em>6.9만 개</em>', t); winIn(t, d, S); zoomTo([800, 20, 800], [1150, 230, 450], sine(seg(t, 0, 1.2))); ringAt(0, 0, 0); chip($('#chipA'), 'MIT 라이선스', 0.6, t); chip($('#chipB'), '무료 오픈소스', 1.3, t); },
  m_wolf(t, d) { meme(t, d, 'm3_wolf', '별 6.9만 개인데<br><em>0원</em>'); },
  step1(t, d, S) { show('L_win'); footage(t, S); titles('① 깃허브에서', '<em>ZIP 받기</em>', t); winIn(t, d, S); zoomTo([300, 100, 1300], [600, 240, 760], sine(seg(t, 0.4, 1.4))); ringAt(0, 0, 0); chip($('#chipA'), 'Code → Download ZIP', 0.9, t); chip($('#chipB'), '', 0, t); },
  step2(t, d, S) { show('L_win'); const up = t > 1.35; footage(t, S, up ? 'src/cl_upload.jpg' : 'src/cl_plugins.jpg'); titles('② 클로드에서', '<em>스킬로 올리기</em>', t); winIn(t, d, S); if (up) zoomTo([0, 0, 1600], [0, 40, 1250], sine(seg(t, 1.35, d))); else zoomTo([200, 0, 1400], [800, 60, 800], sine(seg(t, 0.2, 1.2))); ringAt(0, 0, 0); chip($('#chipA'), '플러그인 → 추가 → 업로드', 0.6, t); chip($('#chipB'), up ? '받은 ZIP 그대로 올리면 끝' : '', 0, t); },
  step3(t, d, S) { show('L_say'); const T0 = S.t0 + t; const a = eo(seg(t, 0, 0.4)); css($('#paste'), { opacity: a, transform: `translateY(${(1 - a) * 60}px) rotateX(${(1 - a) * 20}deg)` }); const w = '휴머나이저로 고쳐 줘'; const n = Math.floor(cl((T0 - EV.say) / 0.9) * w.length); $('#sayT').textContent = w.slice(0, n); $('#sayC').style.opacity = Math.floor(t * 4) % 2 ? 0.2 : 1; const sent = T0 > EV.say + 1.1; css($('#sayBtn'), { background: sent ? 'var(--iris)' : 'rgba(255,255,255,.12)' }); const k = bo(seg(T0, EV.done - 0.05, EV.done + 0.3)); css($('#doneChip'), { transform: `translateX(-50%) scale(${k})`, opacity: seg(T0, EV.done - 0.05, EV.done + 0.05) }); },
  ba(t, d, S) { show('L_win'); footage(t, S); titles('뜻은 그대로', '<em>말투만</em> 사람처럼', t); winIn(t, d, S); zoomTo([60, 230, 1150], [90, 300, 1000], sine(seg(t, 0, d))); ringAt(0, 0, 0); chip($('#chipA'), 'Before → After (README 예시)', 0.6, t); chip($('#chipB'), '', 0, t); },
  mail(t, d, S) { show('L_win'); footage(t, S); titles('영어 메일 보내기 전에', '<em>꼭 한 번</em> 돌려요', t); winIn(t, d, S); zoomTo([90, 300, 1000], [100, 480, 820], sine(seg(t, 0, d))); ringAt(0, 0, 0); chip($('#chipA'), 'After: 사람이 쓴 것처럼', 0.4, t); chip($('#chipB'), '', 0, t); },
  m_cool(t, d) { meme(t, d, 'm1b_sunglass', '보내기 전<br><em>필수 코스</em>'); },
  cta(t, d, S) { show('L_cta'); const T0 = S.t0 + t; const w = '휴먼'; $('#typed').textContent = T0 > EV.type ? w : ''; $('#caret').style.opacity = Math.floor(t * 4) % 2 ? 0.2 : 1; const b = eo(seg(T0, EV.dm, EV.dm + 0.5)); css($('#dm'), { transform: `perspective(1400px) rotateY(${lerp(-60, -4, b)}deg) translateX(${(1 - b) * 300}px)`, opacity: b }); css($('#cbox'), { opacity: eo(seg(t, 0, 0.3)) }); const s = eo(seg(t, 0, 0.4)); css($('#ctaT'), { opacity: s }); },
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
  icon.visible = false; flash(0); $('#shade').style.opacity = S.shade || 0;
  U[S.id] && U[S.id](lt, d, S);
  // global transition flash on scene start
  if (t > 0.2) flash(Math.max(parseFloat($('#flash').style.opacity) || 0, (1 - seg(lt, 0, 0.08)) * (S.cont ? 0 : S.id.startsWith('m_') ? 0.35 : 0.25)));
  dust.rotation.y = t * 0.03; R.render(scene, cam);
  $('#turb').setAttribute('seed', String(Math.floor(t * 30) % 97));
  $('#credit').textContent = S.credit || '';
  captions(t);
}
window.__timelines = { main: { seek: async (t) => { render(t); await Promise.all([fimg.decode().catch(()=>{}), $('#mimg').decode().catch(()=>{})]); }, duration: () => T.dur } };
window.__ready = true; render(0);
