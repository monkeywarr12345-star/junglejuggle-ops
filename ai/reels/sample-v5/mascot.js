// 정글이 — jungle.gcc's own 3D mascot (yellow round body, two jungle leaves, three G·C·C dots on the belly).
// Built from primitives so it renders deterministically in HyperFrames (hf-seek) without external models.
import * as THREE from "three";
import { RoomEnvironment } from "./vendor/RoomEnvironment.js";

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
  const rim = new THREE.DirectionalLight(0xff7a3d, 2.6); rim.position.set(-4, 2.5, -4); scene.add(rim);
  const rim2 = new THREE.DirectionalLight(0xffb36b, 1.2); rim2.position.set(4, 1.5, -3); scene.add(rim2);
  const fill = new THREE.DirectionalLight(0x9fb8ff, 0.35); fill.position.set(3, 0.5, 4); scene.add(fill);
  scene.add(new THREE.AmbientLight(0x2a2220, 0.6));

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
  const eyes = [];
  [-1, 1].forEach((sx) => {
    const e = new THREE.Group(); e.position.set(0.31 * sx, 0.2, 0.86); face.add(e);
    e.add(mesh(new THREE.SphereGeometry(0.15, 32, 24), black, [0, 0, 0], [0.85, 1.15, 0.55]));
    e.add(mesh(new THREE.SphereGeometry(0.045, 16, 12), white, [0.045, 0.07, 0.07]));
    e.add(mesh(new THREE.SphereGeometry(0.022, 12, 8), white, [-0.04, -0.06, 0.07]));
    eyes.push(e);
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

  // state: { x, y, s, ry, wave (0..1), hop (0..1), talk (0..1), blink (0..1), look }
  function renderAt(t, st = {}) {
    const x = st.x ?? 0, y = st.y ?? 0, s = st.s ?? 1;
    root.position.set(x, y, 0); root.scale.setScalar(s);
    floor.position.y = y - 1.02 * s;
    root.rotation.y = (st.ry ?? 0) + Math.sin(t * 0.9) * 0.08;
    const hop = st.hop ?? 0;
    const breathe = Math.sin(t * 2.4) * 0.02;
    bob.position.y = hop * 0.35 + Math.abs(Math.sin(t * 2.4)) * 0.02;
    bob.scale.set(1 - breathe, 1 + breathe + hop * 0.06, 1 - breathe);
    face.rotation.y = (st.look ?? 0) * 0.35;
    leaves.forEach((l, i) => (l.rotation.x = Math.sin(t * 3 + i) * 0.15));
    sprout.rotation.z = Math.sin(t * 2.1) * 0.12;
    const blink = st.blink ?? (((t % 3.2) > 3.05) ? 1 : 0);
    eyes.forEach((e) => (e.scale.y = 1 - 0.9 * blink));
    const talk = st.talk ?? 0;
    const open = talk * (0.5 + 0.5 * Math.abs(Math.sin(t * 13)));
    mouthO.scale.y = 0.01 + open * 0.9; smile.visible = open < 0.15;
    const wave = st.wave ?? 0;
    arms[1].rotation.z = 0.35 + wave * (2.1 + Math.sin(t * 9) * 0.35);
    arms[0].rotation.z = -0.35 - Math.sin(t * 2.4) * 0.05;
    camera.position.set(st.cx ?? 0, st.cy ?? 0.35, st.cz ?? 9);
    camera.lookAt(st.tx ?? 0, st.ty ?? 0.1, 0);
    renderer.render(scene, camera);
  }
  return { renderAt, renderer };
}
