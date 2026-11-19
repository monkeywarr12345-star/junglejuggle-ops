// 정글이 — jungle.gcc's own 3D mascot (yellow round body, two jungle leaves, three G·C·C dots on the belly).
// Built from primitives so it renders deterministically in HyperFrames (hf-seek) without external models.
import * as THREE from "three";
import { RoomEnvironment } from "./vendor/RoomEnvironment.js";
import { RoundedBoxGeometry } from "./vendor/RoundedBoxGeometry.js";

export function createMascot(canvas, W = 1080, H = 1920) {
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1);
  renderer.setSize(W, H, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.32;

  const camera = new THREE.PerspectiveCamera(30, W / H, 0.1, 100);

  // lights: warm key spot from above, orange rim from behind-left, cool fill from right
  const key = new THREE.SpotLight(0xfff1dc, 48, 30, 0.42, 0.55, 1.6);
  key.position.set(1.2, 7.5, 4.5); key.castShadow = true; key.shadow.mapSize.set(1024, 1024); key.shadow.bias = -0.0004; key.shadow.radius = 6;
  scene.add(key, key.target);
  const rim = new THREE.DirectionalLight(0xffd43b, 2.4); rim.position.set(-4, 2.5, -4); scene.add(rim);
  const rim2 = new THREE.DirectionalLight(0x7ee08a, 1.4); rim2.position.set(4, 1.5, -3); scene.add(rim2);
  const fill = new THREE.DirectionalLight(0xd8f0ff, 0.4); fill.position.set(3, 0.5, 4); scene.add(fill);
  scene.add(new THREE.AmbientLight(0x1c3a28, 0.7));

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.ShadowMaterial({ opacity: 0.45 }));
  floor.rotation.x = -Math.PI / 2; floor.position.y = -1.02; floor.receiveShadow = true; scene.add(floor);

  const M = (color, o = {}) => new THREE.MeshPhysicalMaterial({ color, roughness: 0.38, clearcoat: 0.55, clearcoatRoughness: 0.28, ...o });
  const yellow = M(0xffb21a, { sheen: 0.25, sheenColor: new THREE.Color(0xffe08a) });
  const cream = M(0xffe7a8, { roughness: 0.5, clearcoat: 0.2 });
  const deep = M(0xf0a12a);
  const leafM = M(0x3fc35f, { roughness: 0.45 });
  const leafD = M(0x2a9a47, { roughness: 0.5 });
  const black = M(0x14110f, { roughness: 0.18, clearcoat: 1, clearcoatRoughness: 0.05 });
  const white = new THREE.MeshBasicMaterial({ color: 0xffffff });
  const pink = new THREE.MeshPhysicalMaterial({ color: 0xff8fa3, roughness: 0.7, transparent: true, opacity: 0.75 });

  const mesh = (g, m, p = [0, 0, 0], s = [1, 1, 1], r = [0, 0, 0]) => {
    const o = new THREE.Mesh(g, m); o.position.set(...p); o.scale.set(...s); o.rotation.set(...r);
    o.castShadow = true; o.receiveShadow = true; return o;
  };
  const SPH = new THREE.SphereGeometry(1, 64, 48);

  const root = new THREE.Group(); scene.add(root);       // placement (x, y, scale, turn)
  const bob = new THREE.Group(); root.add(bob);          // squash / hop
  const body = mesh(SPH, yellow, [0, 0, 0], [1, 0.92, 0.95]); bob.add(body);
  bob.add(mesh(SPH, cream, [0, -0.42, 0.7], [0.5, 0.36, 0.26]));
  // G·C·C dots
  [[-0.2, 0x4c8df6], [0, 0xe07a52], [0.2, 0x19c37d]].forEach(([x, c]) =>
    bob.add(mesh(new THREE.SphereGeometry(0.07, 24, 16), M(c, { roughness: 0.25, clearcoat: 1 }), [x, -0.42, 0.955], [1, 1, 0.55])));
  // face
  const face = new THREE.Group(); bob.add(face);
  const eyes = [], lids = [];
  [-1, 1].forEach((sx) => {
    const e = new THREE.Group(); e.position.set(0.31 * sx, 0.2, 0.86); face.add(e);
    e.add(mesh(new THREE.SphereGeometry(0.15, 32, 24), black, [0, 0, 0], [0.85, 1.15, 0.55]));
    e.add(mesh(new THREE.SphereGeometry(0.045, 16, 12), white, [0.045, 0.07, 0.07]));
    e.add(mesh(new THREE.SphereGeometry(0.022, 12, 8), white, [-0.04, -0.06, 0.07]));
    eyes.push(e);
    // closed-eye lid (curved line) shown while the eyes are shut
    const lid = mesh(new THREE.TorusGeometry(0.115, 0.026, 12, 32, Math.PI), black, [0.31 * sx, 0.17, 0.9], [1, 0.8, 1], [0, 0, Math.PI]);
    lid.visible = false; face.add(lid); lids.push(lid);
  });
  [-1, 1].forEach((sx) => face.add(mesh(new THREE.SphereGeometry(0.12, 24, 16), pink, [0.55 * sx, 0.0, 0.76], [1, 0.62, 0.32], [0, 0.55 * sx, 0])));
  const smile = mesh(new THREE.TorusGeometry(0.085, 0.024, 12, 32, Math.PI), black, [0, 0.0, 0.93], [1, 1, 1], [0, 0, Math.PI]);
  face.add(smile);
  const mouthO = mesh(new THREE.SphereGeometry(0.07, 24, 16), M(0x5a1e1e, { roughness: 0.6 }), [0, -0.04, 0.915], [1.1, 0.01, 0.4]);
  face.add(mouthO);
  // leaves
  const sprout = new THREE.Group(); sprout.position.set(0, 0.86, 0); bob.add(sprout);
  sprout.add(mesh(new THREE.CylinderGeometry(0.035, 0.045, 0.28, 16), leafD, [0, 0.12, 0]));
  const leaves = [];
  [-1, 1].forEach((sx) => {
    const g = new THREE.Group(); g.position.set(0, 0.26, 0); g.rotation.z = -0.75 * sx; sprout.add(g);
    g.add(mesh(SPH, sx < 0 ? leafM : leafD, [0, 0.3, 0], [0.15, 0.32, 0.06]));
    leaves.push(g);
  });
  // arms + feet
  const arms = [-1, 1].map((sx) => {
    const a = new THREE.Group(); a.position.set(0.9 * sx, -0.12, 0.05); bob.add(a);
    a.add(mesh(new THREE.CapsuleGeometry(0.12, 0.22, 8, 16), yellow, [0.06 * sx, -0.18, 0]));
    a.rotation.z = 0.35 * sx; return a;
  });
  [-1, 1].forEach((sx) => bob.add(mesh(SPH, deep, [0.4 * sx, -0.92, 0.18], [0.27, 0.13, 0.32])));

  // v6: tree stump stage under the feet (+ a little mushroom)
  const rc = document.createElement("canvas"); rc.width = rc.height = 256;
  const r2 = rc.getContext("2d"); r2.fillStyle = "#e2b578"; r2.fillRect(0, 0, 256, 256);
  for (let k = 1; k < 9; k++) { r2.beginPath(); r2.strokeStyle = k % 2 ? "rgba(150,95,45,.55)" : "rgba(170,110,55,.35)"; r2.lineWidth = 3 + (k % 3); r2.arc(128 + (k % 3) - 1, 128, k * 14, 0, Math.PI * 2); r2.stroke(); }
  const ringTex = new THREE.CanvasTexture(rc); ringTex.colorSpace = THREE.SRGBColorSpace;
  const bark = M(0x7a4a26, { roughness: 0.85, clearcoat: 0.05 });
  const topM = new THREE.MeshPhysicalMaterial({ map: ringTex, roughness: 0.7 });
  const stump = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 1.1, 0.36, 48, 1), [bark, topM, bark]);
  stump.position.set(0, -1.23, 0); stump.castShadow = true; stump.receiveShadow = true; root.add(stump);
  [0, 1, 2, 3, 4].forEach((k) => root.add(mesh(new THREE.CylinderGeometry(0.06, 0.1, 0.3, 10), bark, [Math.cos(k * 1.3 + 0.4) * 1.06, -1.3, Math.sin(k * 1.3 + 0.4) * 1.06], [1, 1, 1], [0, 0, 0.5 * Math.cos(k * 1.3)])));
  const mush = new THREE.Group(); mush.position.set(-1.18, -1.41, 0.45); root.add(mush);
  mush.add(mesh(new THREE.CylinderGeometry(0.07, 0.09, 0.22, 16), M(0xfff4dc, { roughness: 0.6 }), [0, 0.11, 0]));
  mush.add(mesh(new THREE.SphereGeometry(0.2, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), M(0xe8473b, { roughness: 0.4 }), [0, 0.2, 0], [1, 0.75, 1]));
  [[0.08, 0.32, 0.1], [-0.1, 0.3, 0.06], [0.0, 0.34, -0.1]].forEach((q) => mush.add(mesh(new THREE.SphereGeometry(0.03, 12, 8), M(0xffffff), q)));

  // Claude-logo cube prop (hook): cream rounded cube with the orange starburst on the front
  const cv = document.createElement("canvas"); cv.width = cv.height = 512;
  const g2 = cv.getContext("2d"); g2.fillStyle = "#f3ece2"; g2.fillRect(0, 0, 512, 512);
  g2.translate(256, 256); g2.fillStyle = "#d97757";
  for (let k = 0; k < 12; k++) { g2.save(); g2.rotate((k * Math.PI * 2) / 12); g2.beginPath(); g2.roundRect(-13, -170, 26, 120, 13); g2.fill(); g2.restore(); }
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
  const side = M(0xf3ece2, { roughness: 0.3, clearcoat: 0.8 });
  const front = new THREE.MeshPhysicalMaterial({ map: tex, roughness: 0.3, clearcoat: 0.8 });
  const cube = new THREE.Mesh(new RoundedBoxGeometry(1, 1, 1, 6, 0.16), [side, side, side, side, front, side]);
  cube.castShadow = true; scene.add(cube);

  // state: { x, y, s, ry, wave (0..1), hop (0..1), talk (0..1), blink (0..1), look, cube (0..1) }
  function renderAt(t, st = {}) {
    const x = st.x ?? 0, y = st.y ?? 0, s = st.s ?? 1;
    root.position.set(x, y, 0); root.scale.setScalar(s);
    floor.position.y = y - 1.41 * s;
    root.rotation.y = (st.ry ?? 0) + Math.sin(t * 0.9) * 0.08;
    const hop = st.hop ?? 0;
    const breathe = Math.sin(t * 2.4) * 0.02;
    bob.position.y = hop * 0.35 + Math.abs(Math.sin(t * 2.4)) * 0.02;
    bob.scale.set(1 - breathe, 1 + breathe + hop * 0.06, 1 - breathe);
    face.rotation.y = (st.look ?? 0) * 0.35;
    leaves.forEach((l, i) => (l.rotation.x = Math.sin(t * 3 + i) * 0.15));
    sprout.rotation.z = Math.sin(t * 2.1) * 0.12;
    const blink = st.blink ?? (((t % 3.2) > 3.05) ? 1 : 0);
    const wide = st.wide ?? 0;
    eyes.forEach((e) => { e.visible = blink < 0.82; e.scale.set(1 + wide * 0.16, (1 - 0.9 * blink) * (1 + wide * 0.22), 1); });
    lids.forEach((l) => (l.visible = blink >= 0.82));
    const talk = st.talk ?? 0;
    const open = talk * (0.5 + 0.5 * Math.abs(Math.sin(t * 13)));
    mouthO.scale.y = 0.01 + open * 0.9; smile.visible = open < 0.15;
    const wave = st.wave ?? 0;
    const point = st.point ?? 0;
    arms[1].rotation.z = 0.35 + wave * (2.1 + Math.sin(t * 9) * 0.35) + point * 1.25;
    arms[0].rotation.z = -0.35 - Math.sin(t * 2.4) * 0.05;
    const cu = st.cube ?? 0; cube.visible = cu > 0.01;
    cube.scale.setScalar(0.44 * cu * s); cube.position.set(x + 0.95 * s, y + (0.55 + Math.sin(t * 1.6) * 0.06) * s, 0.2);
    cube.rotation.set(0.25 + Math.sin(t * 0.9) * 0.08, -0.55 + Math.sin(t * 0.7) * 0.25, 0.12);
    camera.position.set(st.cx ?? 0, st.cy ?? 0.35, st.cz ?? 9);
    camera.lookAt(st.tx ?? 0, st.ty ?? 0.1, 0);
    renderer.render(scene, camera);
  }
  return { renderAt, renderer };
}
