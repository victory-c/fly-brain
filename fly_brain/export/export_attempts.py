"""Every attempt of the CEM run as a one-rider montage page: "Fly learns to ride" / "苍蝇学骑车".

Reads results/attempts/attempts.json plus the gen*.npz the training job has finished writing (a file that
fails to load is skipped: the job is still writing it) and builds a static directory:

  index.html            the page (three.js r128 from the CDNs, the Colnago V4Rs GLB embedded base64 like export_ride3d,
                        the procedural fly rider inlined as its own script block)
  data/index.json       meta + one row per attempt: id, gen, rider, t (end), d (distance), o (outcome), b (brain recording), r (record)
  data/gen{g}.json      per rider the trace rows [x, y, psi, v, phi, delta, steer, power, gust] until a little after t_end
  data/cloud.bin        zlib: uint16 quantised x,y,z per point, then uint8 region per point (same quantisation as brain_payload)
  data/brain/{id}.bin   zlib: uint8 activity (bins x points, 255 = 40 Hz) for the riders with a whole-brain recording

Attempt id = gen * riders + rider + 1. Generations already exported are not redone (--force to redo them); re-run it whenever the job
has written more generations (incremental, a few seconds per new generation; every file is written atomically, the manifest read is retried
while the job rewrites it). A record (r=1) is an attempt that rode further than every attempt before it; the first attempt is the baseline.
Outcome 0 ("finished") with t_end short of the 15 s is the job's logging artefact (its loop stops within one 50 ms log step of
the last fall, so that rider's done row was never written): such attempts are re-labelled from their last state, off the road
when |y| > 3.3 m, else fell.
The page needs a static server with data/ next to index.html (relative URLs, fetch()).

usage: python -m export.export_attempts [results/attempts] [results/attempts_page] [--force] [--bike PATH|none]
"""
import argparse
import base64
import json
import math
import os
import time
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BIKE = ROOT / "assets" / "colnago_v4rs.glb"
NEURONS, SYNAPSES = 166_700, 124_177_616
REG_EN = {"taste": "Gustatory neurons", "feeding": "Subesophageal zone (SEZ)", "smell": "Smell", "memory": "Mushroom body",
          "nav": "Central complex", "vision": "Vision", "touch": "Somatosensory neurons",
          "descending": "Descending neurons", "cord": "Ventral nerve cord", "motor": "Motor neurons", "other": "Other central brain"}
REG_ZH = {"taste": "味觉神经元", "feeding": "食道下区（SEZ）", "smell": "嗅觉", "memory": "蘑菇体", "nav": "中央复合体", "vision": "视觉",
          "touch": "躯体感觉神经元", "descending": "下行神经元", "cord": "腹神经索", "motor": "运动神经元", "other": "中央脑其他"}

HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fly learns to ride</title>
<style>
:root{--pw:340px;--bh:44px;--bmh:230px;--mono:ui-monospace,"SF Mono",Menlo,Consolas,"DejaVu Sans Mono","Noto Sans Mono",monospace;--bg:#e8e9eb;--pbg:#111317;--bbg:#15171b;--fg:#dfe2e7;--dim:#7f858f;--acc:#f0a24a}
html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);font:12px/1.4 var(--mono);overflow:hidden}
#app{display:grid;grid-template-columns:1fr var(--pw);grid-template-rows:1fr var(--bh);height:100%}
#stage{grid-area:1/1/2/2;position:relative;overflow:hidden;min-width:0;min-height:0;background:var(--bg)}
#c{position:absolute;inset:0;width:100%;height:100%;display:block}
#chips{position:absolute;top:10px;left:14px;font-size:9px;letter-spacing:.08em;text-transform:uppercase;color:#6f747c;pointer-events:none}
#hint{position:absolute;top:10px;left:50%;transform:translateX(-50%);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#5d626a;background:rgba(255,255,255,.65);padding:3px 8px;border-radius:3px;pointer-events:none}
.hide{display:none!important}
#panel{grid-area:1/2/3/3;position:relative;background:var(--pbg);display:flex;flex-direction:column;min-height:0;overflow:hidden;border-left:1px solid #000}
/* splitters: drag the grip to change the split, double-click to reset */
#vsplit{position:absolute;left:-5px;top:0;bottom:0;width:10px;cursor:col-resize;z-index:5;touch-action:none}
#hsplit{position:relative;height:8px;flex:none;cursor:row-resize;z-index:5;touch-action:none;background:#0d1017}
#vsplit i,#hsplit i{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);display:block;background:#262a33;border:1px solid #3a3f4a;border-radius:7px;box-shadow:0 1px 4px rgba(0,0,0,.5)}
#vsplit i{width:12px;height:46px}#hsplit i{width:46px;height:12px}
#vsplit i::after,#hsplit i::after{content:'';position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:#7f858f;border-radius:1px}
#vsplit i::after{width:2px;height:18px;box-shadow:3px 0 0 #7f858f,-3px 0 0 #7f858f}#hsplit i::after{width:18px;height:2px;box-shadow:0 3px 0 #7f858f,0 -3px 0 #7f858f}
#vsplit:hover i,#hsplit:hover i,#vsplit.on i,#hsplit.on i{background:#30353f;border-color:var(--acc)}
body.dragging,body.dragging *{user-select:none!important}body.dragv,body.dragv *{cursor:col-resize!important}body.dragh,body.dragh *{cursor:row-resize!important}
#bmap{position:relative;height:var(--bmh);flex:none;background:#0d1017}#bc{width:100%;height:100%;display:block;cursor:grab}
#bnote{position:absolute;left:10px;right:10px;bottom:6px;font-size:9.5px;color:#6b7280;letter-spacing:.02em;pointer-events:none}
#pbody{padding:14px 16px 10px;flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column}
#atitle{font-size:24px;font-weight:600;color:var(--acc);letter-spacing:-.01em;line-height:1.1;font-variant-numeric:tabular-nums}
#atitle.tick{animation:tick .12s}@keyframes tick{0%{color:#fff}100%{color:var(--acc)}}
.tiny{font-size:10px;color:var(--dim);margin-top:5px}.caps{text-transform:uppercase;letter-spacing:.1em}
#stats{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:14px 0 14px}
.lab{font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim)}
.val{font-size:17px;font-weight:600;margin-top:3px;font-variant-numeric:tabular-nums;color:#fff}.val.best{color:var(--acc)}
#card{background:#1c1f26;border-left:2px solid var(--acc);padding:7px 10px;font-size:11.5px;margin-bottom:12px;color:#e9ebef;line-height:1.35}
#status{font-size:18px;font-weight:600;margin:5px 0 10px;color:#fff}
#log{flex:1;min-height:0;overflow:hidden;-webkit-mask-image:linear-gradient(#000 80%,transparent);mask-image:linear-gradient(#000 80%,transparent)}
.ev{margin-bottom:7px}.ev .ts{font-size:9px;color:var(--dim);letter-spacing:.06em;font-variant-numeric:tabular-nums}.ev .tx{font-size:12px;color:#b9bec6}.ev:first-child .tx{color:#fff}
#bar{grid-area:2/1/3/2;background:var(--bbg);display:flex;align-items:center;gap:12px;padding:0 12px;min-width:0;border-top:1px solid #000}
#credits{font-size:9px;letter-spacing:.05em;text-transform:uppercase;color:#6f747c;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:0 1 auto;min-width:0;max-width:28%}
#legend{display:flex;flex-wrap:wrap;gap:3px 9px;font-size:8.5px;color:#8a8f98;white-space:nowrap;flex:none;padding:6px 16px 8px;border-top:1px solid #1b1e24}#legend i{display:inline-block;width:7px;height:7px;border-radius:1px;margin-right:3px;vertical-align:-1px}
#tl{position:relative;flex:1 1 320px;min-width:180px;height:30px}#tlc{width:100%;height:100%;display:block;cursor:pointer}
#tip{position:absolute;bottom:34px;transform:translateX(-50%);background:#22252c;color:#e9ebef;font-size:10px;padding:4px 7px;border-radius:3px;white-space:nowrap;pointer-events:none;border:1px solid #333;z-index:2}
#ctl{display:flex;align-items:center;gap:6px;flex:none}
button,select{font:11px var(--mono);background:#22252c;color:#d9dce1;border:1px solid #30343c;border-radius:3px;padding:0 8px;cursor:pointer;height:24px;line-height:22px}
button:hover{border-color:#666}button.on{background:var(--acc);color:#111;border-color:var(--acc)}
.lang{display:inline-flex;border:1px solid #30343c;border-radius:3px;overflow:hidden;height:24px}.lang button{border:0;border-radius:0;color:#8a8f98;padding:0 7px;height:22px}.lang button+button{border-left:1px solid #30343c}.lang button.on{color:#fff;background:#2c3038}
@media(max-width:1250px){#app{grid-template-rows:1fr auto}#bar{flex-wrap:wrap;padding:6px 10px;row-gap:4px}#tl{flex:1 1 100%;order:3;height:24px}#credits{display:none}}
@media(max-width:1100px){:root{--pw:300px}}
@media(max-width:760px){#app{grid-template-columns:1fr;grid-template-rows:1fr auto 42vh}#stage{grid-area:1/1/2/2}#bar{grid-area:2/1/3/2;flex-wrap:wrap;height:auto;padding:6px 10px;gap:8px}#panel{grid-area:3/1/4/2;border-left:0;border-top:1px solid #000}#bmap{height:110px!important}#vsplit,#hsplit{display:none}#credits,#legend{display:none}#atitle{font-size:20px}}
</style></head><body>
<div id="app">
 <div id="stage"><canvas id="c"></canvas><div id="chips"></div><div id="hint"></div></div>
 <aside id="panel">
  <div id="vsplit"><i></i></div>
  <div id="bmap"><canvas id="bc"></canvas><div id="bnote"></div></div>
  <div id="hsplit"><i></i></div>
  <div id="pbody">
   <div id="atitle">—</div>
   <div class="tiny" id="brainline"></div>
   <div class="tiny caps" id="genline"></div>
   <div id="stats"><div><div class="lab" id="l-dist"></div><div class="val" id="v-dist">0.0 m</div></div><div><div class="lab" id="l-best"></div><div class="val best" id="v-best">0.0 m</div></div><div><div class="lab" id="l-time"></div><div class="val" id="v-time">0:00.0</div></div></div>
   <div id="card" class="hide"></div>
   <div class="lab" id="l-log"></div>
   <div id="status"></div>
   <div id="log"></div>
  </div>
  <div id="legend"></div>
 </aside>
 <div id="bar">
  <div id="credits"></div>
  <div id="tl"><canvas id="tlc"></canvas><div id="tip" class="hide"></div></div>
  <div id="ctl">
   <select id="speed"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option><option value="4">4×</option></select>
   <button id="prev">«</button><button id="play">❚❚</button><button id="next">»</button>
   <button id="sig" class="on"></button><button id="cam"></button>
   <span id="lang" class="lang"><button data-l="en">EN</button><button data-l="zh">中文</button></span>
  </div>
 </div>
</div>
<script id="bikeglb" type="application/octet-stream">__BIKE__</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/DRACOLoader.js"></script>
<script>
// ---- fly.js: the procedural low-poly fly (window.makeFly / window.poseFly), inlined by export_attempts.py ----
// fly.js — procedural low-poly fly rider for three.js r128 (plain script, no modules).
//
//   window.makeFly(opts) -> fly
//   window.poseFly(fly, p)
//
// Axes (same as the bike rig): forward +X, up +Y, the fly's RIGHT side is +Z. Body length 1 unit
// (nose at x=+0.5, abdomen tip near x=-0.5), root origin at the thorax/abdomen junction. The page scales
// fly.root (1.3 m fly on the 0.98 m-wheelbase bike).
//
// fly = {root, head, thorax, abdomen, eyes:[L,R], wings:[L,R], halteres:[L,R], antennae:[L,R],
//        legs:[6 x {hip, knee, upper, lower, foot, len1, len2, hipPos, pole}]  (front-L, front-R, mid-L, mid-R, hind-L, hind-R),
//        standFeet:[6 root-local Vector3], standHeight: 0.44 (root height above ground when standing), materials:{...}}
//
// poseFly(fly, {feet:[6 Vector3 in fly.root's PARENT space (= world when root is a child of the scene)],
//               body:{pos:Vector3, pitch:rad (+ nose down), roll:rad (+ right side down), yaw:rad (+ nose to the fly's left), quaternion?},
//               wings: 0..1 (0 folded over the abdomen, 1 spread), abdomen: droop rad (default 0.18), t: seconds (idle animation),
//               poles: optional [6 Vector3] root-local knee directions (default: outward/up, following the target forward/back)})
// Legs: 2-segment analytic IK from hip to foot target; knee bends outward/up/back like an insect; the foot reaches the target
// exactly when |target-hip| <= len1+len2, otherwise the straight leg points at it.
(function () {
  'use strict';
  var DEG = Math.PI / 180;
  function V3(x, y, z) { return new THREE.Vector3(x, y, z); }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
  function lerp(a, b, u) { return a + (b - a) * u; }
  function mulberry(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

  function makeFly(opts) {
    opts = opts || {};
    var srgb = opts.srgb !== false;                 // convert hex colours to linear (page uses renderer.outputEncoding = sRGBEncoding)
    function col(hex) { var c = new THREE.Color(hex); return srgb ? c.convertSRGBToLinear() : c; }
    function mat(hex, extra) {
      return new THREE.MeshStandardMaterial(Object.assign({ color: col(hex), flatShading: true, roughness: 0.78, metalness: 0.04 }, extra || {}));
    }
    var M = {
      body: mat(opts.bodyColor || 0x48403a),
      head: mat(opts.headColor || 0x4d4540),
      face: mat(0x9d948a, { roughness: 0.6 }),
      eye: mat(opts.eyeColor || 0xd63a1f, { roughness: 0.5, metalness: 0.08 }),
      leg: mat(0x24201d, { roughness: 0.7 }),
      bristle: mat(0x16120f, { roughness: 0.9 }),
      haltere: mat(0xc9ab6c),
      stripe: null, // abdomen uses vertex colours
      abdomen: new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.8, metalness: 0.03 }),
      wing: new THREE.MeshPhysicalMaterial({ color: col(0xc9d8e3), transparent: true, opacity: 0.45, side: THREE.DoubleSide, depthWrite: false,
        roughness: 0.25, metalness: 0.15, clearcoat: 1.0, clearcoatRoughness: 0.15, emissive: col(0x16202a), emissiveIntensity: 0.25 }),
      vein: new THREE.LineBasicMaterial({ color: col(0x55646f), transparent: true, opacity: 0.55 }),
      edge: new THREE.LineBasicMaterial({ color: col(0x6b7a86), transparent: true, opacity: 0.7 })
    };
    var tan = col(0xb9955f), dark = col(0x3e2f24);

    var root = new THREE.Group(); root.name = 'fly';
    var blob = function (rx, ry, rz, material, detail) { var g = new THREE.IcosahedronGeometry(1, detail === undefined ? 1 : detail); g.scale(rx, ry, rz); return new THREE.Mesh(g, material); };

    // ---------------- thorax ----------------
    var thorax = new THREE.Group(); thorax.position.set(0.15, 0.03, 0); root.add(thorax);
    var thoraxMesh = blob(0.20, 0.18, 0.185, M.body); thorax.add(thoraxMesh);
    var scutellum = blob(0.075, 0.05, 0.085, M.body); scutellum.position.set(-0.17, 0.06, 0); thorax.add(scutellum);

    // ---------------- head ----------------
    var head = new THREE.Group(); head.position.set(0.40, -0.01, 0); root.add(head);
    var headMesh = blob(0.10, 0.115, 0.125, M.head); head.add(headMesh);
    var face = blob(0.03, 0.07, 0.05, M.face); face.position.set(0.085, -0.02, 0); head.add(face);
    var eyes = [];
    for (var s = -1; s <= 1; s += 2) {
      var eye = blob(0.08, 0.092, 0.068, M.eye); eye.position.set(0.012, 0.012, s * 0.09); eye.rotation.y = -s * 0.25; head.add(eye); eyes.push(eye);
    }
    var proboscis = new THREE.Mesh(new THREE.ConeGeometry(0.022, 0.09, 4), M.head); proboscis.position.set(0.055, -0.14, 0); proboscis.rotation.z = Math.PI + 0.25; head.add(proboscis);
    var antennae = [];
    for (s = -1; s <= 1; s += 2) {
      var ant = new THREE.Group(); ant.position.set(0.09, 0.0, s * 0.028); head.add(ant);
      var seg = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.009, 0.045, 4), M.head); seg.position.set(0.02, -0.016, 0); seg.rotation.z = 0.9; ant.add(seg);
      var knob = new THREE.Mesh(new THREE.IcosahedronGeometry(0.012, 0), M.head); knob.position.set(0.034, -0.03, 0); ant.add(knob);
      var arista = new THREE.Line(new THREE.BufferGeometry().setFromPoints([V3(0.034, -0.03, 0), V3(0.075, 0.02, s * 0.02)]), M.vein); ant.add(arista);
      antennae.push(ant);
    }

    // ---------------- abdomen (lathe, striped by face colour) ----------------
    var abdomen = new THREE.Group(); abdomen.position.set(0.02, 0.0, 0); root.add(abdomen);
    var abdomenMesh = makeAbdomen(0.52, 0.105, 6, tan, dark, M.abdomen); abdomen.add(abdomenMesh);

    // ---------------- wings ----------------
    var wings = [];
    for (s = -1; s <= 1; s += 2) { var w = makeWing(s, M); w.position.set(0.12, 0.13, s * 0.05); w.rotation.order = 'YXZ'; root.add(w); wings.push(w); }

    // ---------------- halteres ----------------
    var halteres = [];
    for (s = -1; s <= 1; s += 2) {
      var h = new THREE.Group(); h.position.set(-0.02, -0.03, s * 0.12); root.add(h);
      var stalk = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.006, 0.06, 4), M.haltere); stalk.position.set(0, 0.03, 0); h.add(stalk);
      var ball = new THREE.Mesh(new THREE.IcosahedronGeometry(0.015, 0), M.haltere); ball.position.set(0, 0.06, 0); h.add(ball);
      h.quaternion.setFromUnitVectors(V3(0, 1, 0), V3(-0.45, -0.35, s * 0.82).normalize()); h.userData.q0 = h.quaternion.clone();
      halteres.push(h);
    }

    // ---------------- bristles ----------------
    if (opts.bristles !== false) {
      var rnd = mulberry(7);
      addBristles(thorax, rnd, 30, V3(0, 0, 0), V3(0.20, 0.18, 0.185), 0.045, 0.09, 0.3, M.bristle);
      addBristles(head, rnd, 6, V3(-0.02, 0, 0), V3(0.10, 0.115, 0.125), 0.04, 0.06, 0.45, M.bristle);
      addBristles(abdomen, rnd, 10, V3(-0.24, 0, 0), V3(0.25, 0.085, 0.095), 0.035, 0.06, 0.2, M.bristle);
    }

    // ---------------- legs ----------------
    var legDefs = [   // pole = outward/up base; fwd = forward bias of the knee (added to a term that follows the target direction)
      { hip: V3(0.28, -0.11, -0.085), l1: 0.24, l2: 0.34, pole: V3(0.0, 0.8, -1.0), fwd: 0.6 },
      { hip: V3(0.28, -0.11, 0.085), l1: 0.24, l2: 0.34, pole: V3(0.0, 0.8, 1.0), fwd: 0.6 },
      { hip: V3(0.16, -0.125, -0.095), l1: 0.26, l2: 0.38, pole: V3(0.0, 0.8, -1.0), fwd: 0.0 },
      { hip: V3(0.16, -0.125, 0.095), l1: 0.26, l2: 0.38, pole: V3(0.0, 0.8, 1.0), fwd: 0.0 },
      { hip: V3(0.04, -0.11, -0.085), l1: 0.30, l2: 0.44, pole: V3(0.0, 0.8, -1.0), fwd: -0.4 },
      { hip: V3(0.04, -0.11, 0.085), l1: 0.30, l2: 0.44, pole: V3(0.0, 0.8, 1.0), fwd: -0.4 }
    ];
    var legs = legDefs.map(function (d) { var L = makeLeg(root, d.hip, d.l1, d.l2, d.pole.normalize(), M.leg); L.fwd = d.fwd; return L; });

    var standHeight = 0.44;
    var standFeet = [V3(0.44, -standHeight, -0.30), V3(0.44, -standHeight, 0.30), V3(0.12, -standHeight, -0.37), V3(0.12, -standHeight, 0.37), V3(-0.27, -standHeight, -0.34), V3(-0.27, -standHeight, 0.34)];

    var fly = { root: root, head: head, thorax: thorax, abdomen: abdomen, eyes: eyes, wings: wings, halteres: halteres, antennae: antennae,
      legs: legs, standFeet: standFeet, standHeight: standHeight, materials: M, thoraxMesh: thoraxMesh, abdomenMesh: abdomenMesh, headMesh: headMesh };
    poseFly(fly, { wings: 0, t: 0 });   // default: standing on 6 feet (root 0.36 above the ground)
    return fly;
  }

  // Abdomen: lathe around the body axis with 'bands' segments, each a slight bulge; front half of each band 'tan', rear half 'dark'.
  function makeAbdomen(len, R, bands, tan, dark, material) {
    var ctrl = [[0, 0.70], [0.1, 0.90], [0.22, 1.0], [0.40, 1.0], [0.55, 0.93], [0.70, 0.79], [0.82, 0.58], [0.92, 0.34], [1.0, 0.05]];
    function rad(s) { for (var i = 1; i < ctrl.length; i++) if (s <= ctrl[i][0]) { var a = ctrl[i - 1], b = ctrl[i]; return R * lerp(a[1], b[1], (s - a[0]) / (b[0] - a[0])); } return R * ctrl[ctrl.length - 1][1]; }
    var pts = [new THREE.Vector2(0, 0)];
    var bounds = [];
    for (var k = 0; k < bands; k++) {
      var s0 = k / bands, s1 = (k + 1) / bands, sm = (s0 + s1) / 2; bounds.push(s0);
      if (k === 0) pts.push(new THREE.Vector2(rad(s0) * 0.92, s0 * len));
      pts.push(new THREE.Vector2(rad(sm) * 1.0, sm * len));
      pts.push(new THREE.Vector2(rad(s1) * (k === bands - 1 ? 1 : 0.9), s1 * len));
    }
    bounds.push(1);
    pts.push(new THREE.Vector2(0, len * 1.01));
    var g = new THREE.LatheGeometry(pts, 11).toNonIndexed();
    var pos = g.attributes.position, n = pos.count, colors = new Float32Array(n * 3);
    for (var f = 0; f < n; f += 3) {
      var y = (pos.getY(f) + pos.getY(f + 1) + pos.getY(f + 2)) / 3, s = y / len;
      var band = clamp(Math.floor(s * bands), 0, bands - 1), u = (s - bounds[band]) * bands;
      var c = u < 0.5 ? tan : dark;
      for (var v = 0; v < 3; v++) { colors[(f + v) * 3] = c.r; colors[(f + v) * 3 + 1] = c.g; colors[(f + v) * 3 + 2] = c.b; }
    }
    g.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    g.rotateZ(Math.PI / 2);          // lathe axis +Y -> -X (tip points backward)
    g.scale(1, 0.86, 1);             // slightly flattened cross-section
    g.computeVertexNormals();
    return new THREE.Mesh(g, material);
  }

  // Wing: flat low-poly outline in the XZ plane, hinge at the origin, extends toward -X; outward edge toward side*Z.
  function makeWing(side, M) {
    var o = [[0, 0], [-0.04, 0.045], [-0.16, 0.085], [-0.32, 0.098], [-0.47, 0.082], [-0.56, 0.045], [-0.59, 0.0], [-0.55, -0.04], [-0.40, -0.07], [-0.22, -0.077], [-0.08, -0.05], [-0.02, -0.015]];
    var shape = new THREE.Shape(o.map(function (p) { return new THREE.Vector2(p[0], p[1]); }));
    var g = new THREE.ShapeGeometry(shape); g.rotateX(-Math.PI / 2); if (side > 0) g.scale(1, 1, -1);   // (x,y)->(x,0,-y): +y -> -z (left-outward)
    var mesh = new THREE.Mesh(g, M.wing); mesh.renderOrder = 2;
    var pz = function (p) { return V3(p[0], 0.001, side > 0 ? p[1] : -p[1]); };
    var veins = [[0, 0.012], [-0.57, 0.04], [0, 0.0], [-0.52, -0.03], [0, -0.006], [-0.38, -0.068], [-0.2, 0.082], [-0.23, -0.075], [-0.4, 0.09], [-0.43, -0.062]];
    var vg = new THREE.BufferGeometry().setFromPoints(veins.map(pz));
    var edge = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(o.map(pz)), M.edge);
    var pivot = new THREE.Group(); pivot.add(mesh); pivot.add(new THREE.LineSegments(vg, M.vein)); pivot.add(edge); pivot.userData.side = side;
    return pivot;
  }

  // Bristles: thin cones standing on an ellipsoid surface (upper part), tilted backward.
  function addBristles(parent, rnd, n, center, radii, lmin, lmax, minY, material) {
    var up = V3(0, 1, 0), tries = 0;
    for (var i = 0; i < n && tries < n * 30; tries++) {
      var d = V3(rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1); if (d.lengthSq() < 0.05 || d.lengthSq() > 1) continue; d.normalize(); if (d.y < minY) continue;
      var p = V3(d.x * radii.x, d.y * radii.y, d.z * radii.z).add(center);
      var nrm = V3(d.x / radii.x, d.y / radii.y, d.z / radii.z).normalize();
      var dir = nrm.add(V3(-0.7, 0.1, 0)).normalize();
      var len = lerp(lmin, lmax, rnd());
      var g = new THREE.ConeGeometry(0.003, len, 3); g.translate(0, len / 2, 0);
      var b = new THREE.Mesh(g, material); b.position.copy(p); b.quaternion.setFromUnitVectors(up, dir); parent.add(b); i++;
    }
  }

  function makeLeg(root, hip, len1, len2, pole, material) {
    var hipG = new THREE.Group(); hipG.position.copy(hip); root.add(hipG);
    hipG.add(new THREE.Mesh(new THREE.IcosahedronGeometry(0.034, 0), material));                  // coxa
    var ug = new THREE.CylinderGeometry(0.019, 0.014, len1, 5); ug.translate(0, -len1 / 2, 0);
    var upper = new THREE.Mesh(ug, material); hipG.add(upper);                                     // femur
    var kneeG = new THREE.Group(); kneeG.position.set(0, -len1, 0); hipG.add(kneeG);
    kneeG.add(new THREE.Mesh(new THREE.IcosahedronGeometry(0.017, 0), material));
    var lg = new THREE.CylinderGeometry(0.012, 0.0065, len2, 5); lg.translate(0, -len2 / 2, 0);
    var lower = new THREE.Mesh(lg, material); kneeG.add(lower);                                    // tibia + tarsus
    var foot = new THREE.Object3D(); foot.position.set(0, -len2, 0); kneeG.add(foot);
    foot.add(new THREE.Mesh(new THREE.IcosahedronGeometry(0.011, 0), material));
    return { hip: hipG, knee: kneeG, upper: upper, lower: lower, foot: foot, len1: len1, len2: len2, hipPos: hip.clone(), pole: pole.clone() };
  }

  // ---- IK (root-local space) ----
  var _d = new THREE.Vector3(), _p = new THREE.Vector3(), _k = new THREE.Vector3(), _u = new THREE.Vector3(), _down = new THREE.Vector3(0, -1, 0),
      _q1 = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _m = new THREE.Matrix4(), _tg = new THREE.Vector3(), _pl = new THREE.Vector3(), _pv = new THREE.Vector3();
  function solveLeg(leg, target, pole) {
    var H = leg.hipPos, l1 = leg.len1, l2 = leg.len2;
    _d.subVectors(target, H); var L = _d.length(); if (L < 1e-6) { _d.set(0, -1, 0); L = 1e-6; } _d.multiplyScalar(1 / L);
    if (pole) _pl.copy(pole); else { _pl.copy(leg.pole); _pl.x += 0.9 * clamp(_d.x / 0.25, -1, 1) + (leg.fwd || 0); }   // knee follows the target: forward target -> forward knee
    if (L >= l1 + l2 - 1e-5) { _k.copy(H).addScaledVector(_d, l1); }
    else {
      var Lc = Math.max(L, Math.abs(l1 - l2) + 1e-4);
      var cosA = clamp((l1 * l1 + Lc * Lc - l2 * l2) / (2 * l1 * Lc), -1, 1), A = Math.acos(cosA);
      _p.copy(_pl).addScaledVector(_d, -_pl.dot(_d));
      if (_p.lengthSq() < 1e-6) { _p.set(0, 1, 0).addScaledVector(_d, -_d.y); if (_p.lengthSq() < 1e-6) _p.set(1, 0, 0); }
      _p.normalize();
      _k.copy(H).addScaledVector(_d, l1 * Math.cos(A)).addScaledVector(_p, l1 * Math.sin(A));
    }
    _u.subVectors(_k, H).normalize(); _q1.setFromUnitVectors(_down, _u);
    _u.subVectors(target, _k).normalize(); _q2.setFromUnitVectors(_down, _u);
    leg.hip.quaternion.copy(_q1);
    leg.knee.quaternion.copy(_q1).invert().multiply(_q2);
  }

  function poseFly(fly, p) {
    p = p || {};
    var root = fly.root, t = p.t || 0;
    if (p.body) {
      var b = p.body;
      if (b.pos) root.position.copy(b.pos);
      if (b.quaternion) root.quaternion.copy(b.quaternion);
      else { root.rotation.order = 'YZX'; root.rotation.set(b.roll || 0, b.yaw || 0, -(b.pitch || 0)); }
    }
    root.updateMatrix();
    var inv = p.feet ? _m.copy(root.matrix).invert() : null;
    for (var i = 0; i < 6; i++) {
      var tgt = p.feet && p.feet[i] ? _tg.copy(p.feet[i]).applyMatrix4(inv) : fly.standFeet[i];
      solveLeg(fly.legs[i], tgt, p.poles && p.poles[i] ? _pv.copy(p.poles[i]) : null);   // poles: optional root-local knee directions
    }
    // wings: 0 folded flat along the abdomen, 1 spread; buzz when spread
    var droop = p.abdomen === undefined ? 0.18 : p.abdomen;
    var w = clamp(p.wings === undefined ? 0 : p.wings, 0, 1), flutter = w * 0.22 * Math.sin(t * 75) + (1 - w) * 0.008 * Math.sin(t * 9);
    for (i = 0; i < 2; i++) {
      var wg = fly.wings[i], s = wg.userData.side;
      wg.rotation.y = s * lerp(7 * DEG, 74 * DEG, w);
      wg.rotation.x = -s * (lerp(0.03, 14 * DEG, w) + flutter);
      wg.rotation.z = lerp(droop + 0.05, -4 * DEG, w);
      wg.position.y = 0.13 + 0.01 * w;
    }
    for (i = 0; i < 2; i++) { var h = fly.halteres[i]; h.quaternion.copy(h.userData.q0); h.rotateX(0.35 * w * Math.sin(t * 75 + Math.PI)); }
    // idle: breathing abdomen, head and antennae micro-motion
    var breath = Math.sin(t * 2.6);
    fly.abdomen.rotation.z = droop + 0.012 * breath;
    fly.abdomen.scale.set(1, 1 + 0.02 * breath, 1 + 0.015 * breath);
    fly.head.rotation.y = 0.05 * Math.sin(t * 0.9); fly.head.rotation.z = 0.025 * Math.sin(t * 1.3 + 1);
    for (i = 0; i < 2; i++) fly.antennae[i].rotation.z = 0.1 * Math.sin(t * 2.1 + i * 1.7);
  }

  window.makeFly = makeFly;
  window.poseFly = poseFly;
  window.flySolveLeg = solveLeg;
})();
</script>
<script>
'use strict';
const $=id=>document.getElementById(id);
const V=(x,y,z=0)=>new THREE.Vector3(x,y,z);
// =====================================================================================================
// language: ?lang=en|zh (saved), else localStorage 'flybrain.lang', else the browser language. Every visible string lives here.
// =====================================================================================================
const OUT_EN=['finished','fell','off the road','bailed'],OUT_ZH=['骑满','倒了','出界','跳车'];
const I18N={
en:{title:'Fly learns to ride',chips:'Male CNS v1.0 · 166,700 neurons · connectome unchanged · Whipple physics on',
 attempt:k=>'Attempt #'+k,brainline:'166,700 neurons · 124M synapses',genline:(g,r)=>'Generation '+g+' · Rider '+r,
 dist:'Distance',best:'Best',time:'Time',log:'Action log',
 noRec:'No whole-brain recording for this attempt',rec:'Whole-brain recording · bright = fired in this 100 ms · drag to rotate',loadingRec:'Loading the whole-brain recording…',
 climb:'Climb on the bike',pedal:'Pedal',mark:m=>m+' m',gustL:'Gust from the left',gustR:'Gust from the right',wobL:'Wobble left, corrected',wobR:'Wobble right, corrected',
 driftL:'Drifting left',driftR:'Drifting right',centre:'Back to the centre',record:'New record',up:'Still upright',
 fell:'Fell',off:'Off the road',bail:'Jumped off (giant fibre)',fin:'Finished the 15 s',riding:'Riding',
 card:(k,o,t,d)=>'Attempt #'+k+': '+(o===0?'finished the 15 s':(o===1?'fell':o===2?'off the road':'jumped off')+' after '+t.toFixed(1)+' s')+', '+d.toFixed(1)+' m',
 skip:n=>'Skipping '+n+' ordinary attempt'+(n===1?'':'s')+'…',
 tip:a=>'Attempt #'+a.id+' · gen '+a.gen+' rider '+a.rider+' · '+a.d.toFixed(1)+' m · '+OUT_EN[a.o]+(a.o===0?'':' at '+a.t.toFixed(1)+' s')+(a.r?' · record':''),
 play:'Play (space)',pause:'Pause (space)',prev:'Previous attempt (←)',next:'Next attempt (→)',sigOn:'Significant only',sigOff:'All attempts',
 sigT:'Significant attempts: the first, every new record, the mean rider of each generation, its earliest and its longest failure, the last. The rest are flipped through.',
 speed:'Playback speed (keys 1 2 4 · 5 = ½× · [ ] slower/faster)',camSide:'Side',camChase:'Chase',camQuarter:'¾ view',camT:'Camera (c)',lang:'Language',
 credits:'flybrain-play · male CNS v1.0 · Colnago V4Rs',loading:'Loading…',loadingBike:'Loading the bike model…',noData:'No attempts yet',
 lgFell:'fell',lgOff:'off road',lgFin:'finished',lgBail:'bailed',lgRec:'record',
 splitV:'Drag to resize the panel · double-click to reset',splitH:'Drag to resize the brain map · double-click to reset'},
zh:{title:'苍蝇学骑车',chips:'雄性 CNS v1.0 · 166,700 神经元 · 连接组不变 · Whipple 物理开',
 attempt:k=>'第 '+k+' 次尝试',brainline:'166,700 神经元 · 1.24 亿突触',genline:(g,r)=>'第 '+g+' 代 · 骑手 '+r,
 dist:'里程',best:'最佳',time:'时间',log:'动作记录',
 noRec:'这次没有全脑记录',rec:'全脑记录 · 亮点 = 这 100 ms 里放电的神经元 · 拖动旋转',loadingRec:'正在加载全脑记录…',
 climb:'上车',pedal:'踩踏',mark:m=>m+' m',gustL:'左边来阵风',gustR:'右边来阵风',wobL:'向左晃，纠正了',wobR:'向右晃，纠正了',
 driftL:'向左偏',driftR:'向右偏',centre:'回到路中间',record:'新纪录',up:'还没倒',
 fell:'倒了',off:'出界',bail:'跳车（巨大纤维）',fin:'骑满 15 秒',riding:'骑行中',
 card:(k,o,t,d)=>'第 '+k+' 次尝试：'+(o===0?'骑满 15 秒':t.toFixed(1)+' 秒后'+(o===1?'倒了':o===2?'出界':'跳车'))+'，'+d.toFixed(1)+' m',
 skip:n=>'快进 '+n+' 次普通尝试…',
 tip:a=>'第 '+a.id+' 次尝试 · 第 '+a.gen+' 代 骑手 '+a.rider+' · '+a.d.toFixed(1)+' m · '+(a.o===0?'骑满':a.t.toFixed(1)+' 秒'+OUT_ZH[a.o])+(a.r?' · 纪录':''),
 play:'播放（空格）',pause:'暂停（空格）',prev:'上一次（←）',next:'下一次（→）',sigOn:'只看关键尝试',sigOff:'所有尝试',
 sigT:'关键尝试：第一次、每个新纪录、每代的均值骑手、每代最早和最久的失败、最后一次。其余快进跳过。',
 speed:'播放速度（按键 1 2 4 · 5 = ½× · [ ] 减速/加速）',camSide:'侧拍',camChase:'跟拍',camQuarter:'斜拍',camT:'镜头（c）',lang:'语言',
 credits:'flybrain-play · 雄性 CNS v1.0 · Colnago V4Rs',loading:'加载中…',loadingBike:'加载车模…',noData:'还没有尝试',
 lgFell:'倒了',lgOff:'出界',lgFin:'骑满',lgBail:'跳车',lgRec:'纪录',
 splitV:'拖动调节侧栏宽度 · 双击复位',splitH:'拖动调节脑图高度 · 双击复位'}};
const LS={get:k=>{try{return localStorage.getItem(k)}catch(e){return null}},set:(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}}};
const Q=new URLSearchParams(location.search);
let LANG=(()=>{const q=Q.get('lang');if(q==='en'||q==='zh'){LS.set('flybrain.lang',q);return q}
 const s=LS.get('flybrain.lang');if(s==='en'||s==='zh')return s;return /^zh/i.test(navigator.language||'')?'zh':'en'})();
function tt(k,...a){const v=I18N[LANG][k];return typeof v==='function'?v(...a):(v===undefined?k:v)}
const LANG_HOOKS=[];
function applyLang(){document.documentElement.lang=LANG==='zh'?'zh-CN':'en';document.title=tt('title');
 $('chips').textContent=tt('chips');$('brainline').textContent=tt('brainline');
 for(const k of['dist','best','time','log'])$('l-'+k).textContent=tt(k);
 $('credits').textContent=tt('credits');
 $('legend').innerHTML=[['lgFell',COL[1]],['lgOff',COL[2]],['lgFin',COL[0]],['lgBail',COL[3]],['lgRec','#fff']].map(([k,c])=>'<span><i style="background:'+c+'"></i>'+tt(k)+'</span>').join('');
 $('prev').title=tt('prev');$('next').title=tt('next');$('speed').title=tt('speed');$('lang').title=tt('lang');$('cam').title=tt('camT');
 $('sig').title=tt('sigT');$('vsplit').title=tt('splitV');$('hsplit').title=tt('splitH');
 for(const b of document.querySelectorAll('#lang button'))b.classList.toggle('on',b.dataset.l===LANG);
 for(const f of LANG_HOOKS)f()}
function setLang(l){if(l===LANG||!I18N[l])return;LANG=l;LS.set('flybrain.lang',l);
 try{const u=new URL(location.href);if(u.searchParams.has('lang')){u.searchParams.set('lang',l);history.replaceState(history.state,'',u)}}catch(e){}applyLang()}
for(const b of document.querySelectorAll('#lang button'))b.onclick=()=>setLang(b.dataset.l);
const COL=['#3fb950','#e5484d','#f0883e','#a371f7'];  // finished, fell, off the road, bailed
// splitters: panel width (--pw) and brain-map height (--bmh), remembered per browser; the renderers follow via ResizeObserver
(function(){const root=document.documentElement.style,panel=$('panel');
 const lim={pw:()=>[240,Math.max(240,Math.min(innerWidth*0.7,1000))],bmh:()=>[90,Math.max(90,panel.clientHeight-230)]};
 const setv=(k,v)=>{const [lo,hi]=lim[k]();v=Math.round(Math.max(lo,Math.min(hi,v)));root.setProperty('--'+k,v+'px');return v};
 if(innerWidth>760){const pw=+LS.get('flybrain.attempts.pw'),bmh=+LS.get('flybrain.attempts.bmh');if(pw)setv('pw',pw);if(bmh)setv('bmh',bmh)}
 function wire(id,k,cls,delta){const h=$(id);let x0=0,y0=0,v0=0;
  h.addEventListener('pointerdown',e=>{if(e.button)return;e.preventDefault();x0=e.clientX;y0=e.clientY;v0=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--'+k))||0;
   h.classList.add('on');document.body.classList.add('dragging',cls);try{h.setPointerCapture(e.pointerId)}catch(err){}});
  h.addEventListener('pointermove',e=>{if(!h.classList.contains('on'))return;setv(k,v0+delta(e.clientX-x0,e.clientY-y0))});
  const end=e=>{if(!h.classList.contains('on'))return;h.classList.remove('on');document.body.classList.remove('dragging',cls);
   LS.set('flybrain.attempts.'+k,String(setv(k,v0+delta(e.clientX-x0,e.clientY-y0))))};
  h.addEventListener('pointerup',end);h.addEventListener('pointercancel',end);
  h.addEventListener('dblclick',()=>{root.removeProperty('--'+k);LS.set('flybrain.attempts.'+k,'')})}
 wire('vsplit','pw','dragv',(dx,dy)=>-dx);wire('hsplit','bmh','dragh',(dx,dy)=>dy);
 addEventListener('resize',()=>{for(const k of['pw','bmh']){const v=parseFloat(root.getPropertyValue('--'+k));if(v)setv(k,v)}})})();
const fmtD=d=>d.toFixed(1)+' m',fmtT=t=>{const m=Math.floor(t/60),s=t-60*m;return m+':'+(s<10?'0':'')+s.toFixed(1)};
const ease=u=>u*u*(3-2*u);
// =====================================================================================================
// data: data/index.json (meta + attempts), data/gen{g}.json on demand (4 cached), data/brain/{id}.bin per attempt, data/cloud.bin once
// =====================================================================================================
let META=null,ATT=[],SIG=new Set(),BB=[],DMAX=1;
async function inflate(resp){return new Uint8Array(await new Response(resp.body.pipeThrough(new DecompressionStream('deflate'))).arrayBuffer())}
const genCache=new Map();
function loadGen(g){if(genCache.has(g))return genCache.get(g);
 const p=fetch('data/gen'+g+'.json').then(r=>{if(!r.ok)throw new Error('gen '+g+' '+r.status);return r.json()});
 p.catch(()=>genCache.delete(g));genCache.set(g,p);
 if(genCache.size>4){for(const k of genCache.keys()){if(k!==g&&!(ST.att&&k===ST.att.gen)){genCache.delete(k);break}}}
 return p}
const brainCache=new Map();
function loadBrainBin(id){if(brainCache.has(id))return brainCache.get(id);
 const p=fetch('data/brain/'+id+'.bin').then(r=>{if(!r.ok)throw new Error('brain '+id+' '+r.status);return inflate(r)});
 p.catch(()=>brainCache.delete(id));brainCache.set(id,p);if(brainCache.size>3){for(const k of brainCache.keys()){if(k!==id){brainCache.delete(k);break}}}return p}
function computeSig(){SIG=new Set();if(!ATT.length)return;SIG.add(0);SIG.add(ATT.length-1);let best=-1;const byGen=new Map();
 ATT.forEach((a,i)=>{if(a.d>best){best=a.d;SIG.add(i)}if(a.rider===0)SIG.add(i);
  if(a.o!==0){const g=byGen.get(a.gen)||{e:-1,l:-1};if(g.e<0||a.t<ATT[g.e].t)g.e=i;if(g.l<0||a.t>ATT[g.l].t)g.l=i;byGen.set(a.gen,g)}});
 for(const g of byGen.values()){SIG.add(g.e);SIG.add(g.l)}
 let b=0;BB=ATT.map(a=>{const r=b;b=Math.max(b,a.d);return r});DMAX=Math.max(1,...ATT.map(a=>a.d))}
// =====================================================================================================
// scene: light grey world, fine floor grid, the 7 m road with a dashed centre line, cones, painted distance marks
// =====================================================================================================
const canvas=$('c'),stage=$('stage');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputEncoding=THREE.sRGBEncoding;
const BG=0xe8e9eb,scene=new THREE.Scene();scene.background=new THREE.Color(BG);scene.fog=new THREE.Fog(BG,26,90);
const camera=new THREE.PerspectiveCamera(38,1,0.1,300);
scene.add(new THREE.HemisphereLight(0xffffff,0xd6d7da,0.62));
const sun=new THREE.DirectionalLight(0xffffff,0.46);sun.position.set(-6,16,8);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.bias=-0.0006;sun.shadow.radius=4;
Object.assign(sun.shadow.camera,{left:-9,right:9,top:9,bottom:-9,near:1,far:60});scene.add(sun);scene.add(sun.target);
const flat=(c,o={})=>{const m=new THREE.MeshStandardMaterial(Object.assign({roughness:.95,metalness:0},o));m.color.setHex(c).convertSRGBToLinear();return m};
const XMIN=-40,XMAX=200,XC=(XMIN+XMAX)/2,XL=XMAX-XMIN,ROAD_W=7;
function gridTex(){const c=document.createElement('canvas');c.width=c.height=256;const x=c.getContext('2d');x.fillStyle='#e2e3e6';x.fillRect(0,0,256,256);
 x.fillStyle='#d6d8dc';x.fillRect(0,127,256,1);x.fillRect(127,0,1,256);x.fillStyle='#bfc2c8';x.fillRect(0,0,256,2);x.fillRect(0,0,2,256);
 const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(XL,200);t.anisotropy=renderer.capabilities.getMaxAnisotropy();t.encoding=THREE.sRGBEncoding;return t}
const gridT=gridTex(),roadT=gridT.clone();roadT.repeat.set(XL,ROAD_W);roadT.offset.set(0,0.5);roadT.needsUpdate=true;
const floor=new THREE.Mesh(new THREE.PlaneGeometry(XL,200),new THREE.MeshStandardMaterial({map:gridT,roughness:1,metalness:0}));floor.rotation.x=-Math.PI/2;floor.position.set(XC,0,0);floor.receiveShadow=true;scene.add(floor);
const road=new THREE.Mesh(new THREE.PlaneGeometry(XL,ROAD_W),flat(0xe4e6ea,{map:roadT}));road.rotation.x=-Math.PI/2;road.position.set(XC,0.004,0);road.receiveShadow=true;scene.add(road);
const lineM=flat(0xf7f7f8);
for(const z of[-ROAD_W/2+0.05,ROAD_W/2-0.05]){const e=new THREE.Mesh(new THREE.PlaneGeometry(XL,0.08),lineM);e.rotation.x=-Math.PI/2;e.position.set(XC,0.006,z);scene.add(e)}
{const n=Math.ceil(XL/6),d=new THREE.InstancedMesh(new THREE.PlaneGeometry(2.4,0.1),lineM,n),m=new THREE.Matrix4();for(let i=0;i<n;i++){m.makeRotationX(-Math.PI/2);m.setPosition(XMIN+i*6+3,0.006,0);d.setMatrixAt(i,m)}scene.add(d)}
{const s=new THREE.Mesh(new THREE.PlaneGeometry(0.16,ROAD_W),lineM);s.rotation.x=-Math.PI/2;s.position.set(0,0.0065,0);scene.add(s)}  // start line
{const coneG=new THREE.ConeGeometry(0.17,0.52,7);coneG.translate(0,0.26,0);const baseG=new THREE.BoxGeometry(0.38,0.03,0.38);baseG.translate(0,0.015,0);
 const xs=[];for(let x=0;x<=XMAX-10;x+=10)xs.push(x);const n=xs.length*2,cones=new THREE.InstancedMesh(coneG,flat(0xf0742a),n),bases=new THREE.InstancedMesh(baseG,flat(0xd2602a),n),m=new THREE.Matrix4();
 xs.forEach((x,i)=>{for(const [j,z] of[[0,-ROAD_W/2],[1,ROAD_W/2]]){m.makeRotationY(i*0.7+j);m.setPosition(x,0,z);cones.setMatrixAt(2*i+j,m);bases.setMatrixAt(2*i+j,m)}});
 cones.castShadow=bases.castShadow=true;scene.add(cones);scene.add(bases)}
function markTex(txt){const c=document.createElement('canvas');c.width=256;c.height=96;const x=c.getContext('2d');x.fillStyle='#8d9199';x.font='bold 58px ui-monospace,Menlo,Consolas,"DejaVu Sans Mono",monospace';x.textAlign='center';x.textBaseline='middle';x.fillText(txt,128,50);
 const t=new THREE.CanvasTexture(c);t.encoding=THREE.sRGBEncoding;t.anisotropy=renderer.capabilities.getMaxAnisotropy();return t}
for(let x=5;x<=XMAX-10;x+=5){const p=new THREE.Mesh(new THREE.PlaneGeometry(1.7,0.64),new THREE.MeshBasicMaterial({map:markTex(x+' m'),transparent:true,depthWrite:false}));p.rotation.x=-Math.PI/2;p.position.set(x,0.008,-2.1);scene.add(p)}
// =====================================================================================================
// the bike: the embedded Colnago V4Rs (Draco GLB) rigged like export_ride3d: fork + bars + front wheel steer about the head-tube axis,
// wheels and crank spin. Roll frame: origin at the rear contact point, x forward, y up, z to the rider's right, metres.
// =====================================================================================================
let MODEL=null,G=null,bike=null,rider=null;
const SN=n=>THREE.PropertyBinding.sanitizeNodeName(n);  // GLTFLoader renames nodes: spaces -> _, drops []:./
const Z=V(0,0,1),_q=new THREE.Quaternion(),_w=new THREE.Vector3();
function spin(p,a){p.quaternion.copy(p.userData.q0).multiply(_q.setFromAxisAngle(Z,a))}
function tube(g,a,b,r,m){const d=new THREE.Vector3().subVectors(b,a),l=Math.max(d.length(),1e-4);const c=new THREE.Mesh(new THREE.CylinderGeometry(r,r,1,10),m);c.scale.y=l;c.position.copy(a).addScaledVector(d,0.5);c.quaternion.setFromUnitVectors(V(0,1,0),d.clone().normalize());c.castShadow=true;g.add(c);return c}
function setTube(c,a,b){const d=new THREE.Vector3().subVectors(b,a),l=Math.max(d.length(),1e-4);c.position.copy(a).addScaledVector(d,0.5);c.scale.set(1,l,1);c.quaternion.setFromUnitVectors(V(0,1,0),d.divideScalar(l))}
function procGeo(){ // fallback when the model cannot be decoded: Tarmac SL9 56 cm numbers
 return {name:'procedural',R:0.336,LAM:16.5*Math.PI/180,RH:V(0,0.336),FH:V(0.981,0.336),BB:V(0.405,0.264),SAD:V(0.20,0.975),HT:V(0.785,0.85),HB:V(0.826,0.71),HOOD:V(0.96,0.905),hoodZ:0.19,crankLen:0.1725,crank0:0}}
function modelGeo(){ // every point read off the model's own anchors and part bounding boxes
 const m=MODEL;m.updateMatrixWorld(true);const by=n=>m.getObjectByName(SN(n));const wp=n=>by(n).getWorldPosition(V(0,0));
 const bb=names=>{const b=new THREE.Box3();for(const n of names){const o=by(n);if(o)b.expandByObject(o)}return b};
 const RH=wp('anchor_frame_rearhub'),FH=wp('anchor_frame_fronthub'),BB=wp('anchor_frame_bottom_bracket');
 const tyre=bb(['Tyre Pzero001','Tyre Pzero']);const R=(tyre.max.y-tyre.min.y)/2;const off=V(-RH.x,-(RH.y-R),-RH.z);
 const o2=v=>V(v.x+off.x,v.y+off.y,0);
 const sad=bb(['Dummy_Saddle_ProLogo_Scratch']),cap=bb(['head tube cap001 RVBU']).getCenter(V(0,0)),hood=bb(['RightHandle']),arm=bb(['crank armLogo2']).getCenter(V(0,0));
 const LAM=18*Math.PI/180;  // 72 deg head angle: puts the front hub 48.6 mm (fork rake) ahead of the steering axis through the headset cap
 const HT=o2(cap),HB=HT.clone().add(V(Math.sin(LAM)*0.15,-Math.cos(LAM)*0.15));
 return {name:'Colnago V4Rs',R,LAM,off,RH:o2(RH),FH:o2(FH),BB:o2(BB),SAD:o2(V((sad.min.x+sad.max.x)/2,sad.max.y)),HT,HB,
  HOOD:o2(V((hood.min.x+hood.max.x)/2,hood.max.y)),hoodZ:(hood.min.z+hood.max.z)/2,crankLen:0.1725,crank0:Math.atan2(arm.y-BB.y,arm.x-BB.x)}}
function rigModel(){const m=MODEL,g=G,root=new THREE.Group();root.add(m);m.position.copy(g.off);root.updateMatrixWorld(true);
 const by=n=>m.getObjectByName(SN(n));
 const mk=(parent,at)=>{const p=new THREE.Group();p.position.copy(at);parent.add(p);root.updateMatrixWorld(true);return p};
 const group=(at,names)=>{const p=mk(root,at);for(const n of names){const o=by(n);if(o){root.updateMatrixWorld(true);p.attach(o)}}p.userData.q0=p.quaternion.clone();return p};
 const tilt=mk(root,g.HB);tilt.rotation.z=g.LAM;const steer=new THREE.Group();tilt.add(steer);root.updateMatrixWorld(true);
 const fs=group(g.FH,['Dummy_Wheel_BoraWTO_Front','disc_break_front01','disc_break_front02']);
 for(const n of['V4_510_SDM3_Fork004_RVBU','anchor_frame_fronthub','anchor_frame_handlebar','Stem top bracket RVBU','V4_510_SDM3_Club_Front_004_RVBU']){const o=by(n);if(o){root.updateMatrixWorld(true);steer.attach(o)}}
 root.updateMatrixWorld(true);steer.attach(fs);fs.userData.q0=fs.quaternion.clone();
 const rs=group(g.RH,['Dummy_Wheel_BoraWTO_Back','reardiscA','reardiscB','disc_break_rear03']);
 const cs=group(g.BB,['crank arm part 01','crank armLogo','crank armLogo2','CogOuter','CrankInner','CrankOuter','chain ring text']);
 const handL=mk(root,V(g.HOOD.x,g.HOOD.y,-g.hoodZ)),handR=mk(root,V(g.HOOD.x,g.HOOD.y,g.hoodZ));steer.attach(handL);steer.attach(handR);
 const paintMats=[];m.traverse(o=>{if(o.isMesh){o.castShadow=true;if(o.material&&o.material.name==='RVBU'&&!paintMats.includes(o.material))paintMats.push(o.material)}});
 for(const pm of paintMats){pm.userData.paint=true;pm.userData.orig=pm.color.getHex()}
 return {root,steer,fs,rs,cs,hands:[handL,handR]}}
function procRig(){ // a plain bike when the GLB cannot be decoded: two wheels, a frame of tubes, bars
 const g=G,root=new THREE.Group(),black=flat(0x1a1a1c),paint=flat(0xc8102e);
 const wheel=at=>{const w=new THREE.Group();w.position.copy(at);const t=new THREE.Mesh(new THREE.TorusGeometry(g.R-0.012,0.013,10,48),black);t.castShadow=true;w.add(t);
  for(let i=0;i<12;i++){const sp=new THREE.Mesh(new THREE.BoxGeometry(0.003,2*g.R-0.06,0.002),flat(0x999999));sp.rotation.z=i/12*Math.PI;w.add(sp)}w.userData.q0=w.quaternion.clone();return w};
 const rs=wheel(g.RH);root.add(rs);
 tube(root,g.HB,g.BB,0.03,paint);tube(root,g.BB,g.SAD,0.025,paint);tube(root,g.SAD,g.HT,0.022,paint);tube(root,g.HT,g.HB,0.03,paint);
 for(const z of[-0.05,0.05]){tube(root,V(g.BB.x,g.BB.y,z),V(g.RH.x,g.RH.y,z),0.01,paint);tube(root,V(g.RH.x,g.RH.y,z),V(g.SAD.x+0.02,g.SAD.y-0.06,z*0.6),0.008,paint)}
 const sad=new THREE.Mesh(new THREE.BoxGeometry(0.26,0.03,0.13),black);sad.position.copy(g.SAD).add(V(-0.02,-0.015));root.add(sad);
 const tilt=new THREE.Group();tilt.position.copy(g.HB);tilt.rotation.z=g.LAM;root.add(tilt);const steer=new THREE.Group();tilt.add(steer);const un=new THREE.Group();un.rotation.z=-g.LAM;steer.add(un);
 const rel=v=>V(v.x-g.HB.x,v.y-g.HB.y,v.z||0);for(const z of[-0.045,0.045])tube(un,V(0,-0.03,z),V(g.FH.x-g.HB.x,g.FH.y-g.HB.y,z),0.011,paint);
 const fs=wheel(rel(g.FH));un.add(fs);tube(un,rel(g.HT),rel(V(g.HOOD.x-0.08,g.HOOD.y-0.02)),0.016,black);
 const bar=new THREE.Mesh(new THREE.BoxGeometry(0.04,0.025,2*g.hoodZ+0.04),black);bar.position.copy(rel(V(g.HOOD.x-0.06,g.HOOD.y-0.02)));un.add(bar);
 const hands=[];for(const s of[-1,1]){const h=new THREE.Group();h.position.copy(rel(V(g.HOOD.x,g.HOOD.y,s*g.hoodZ)));un.add(h);hands.push(h)}
 const cs=new THREE.Group();cs.position.copy(g.BB);root.add(cs);cs.userData.q0=cs.quaternion.clone();
 for(const s of[-1,1]){const arm=new THREE.Mesh(new THREE.BoxGeometry(g.crankLen,0.02,0.012),black);arm.position.set(g.crankLen/2*s,0,s*0.075);cs.add(arm)}
 root.traverse(o=>{if(o.isMesh)o.castShadow=true});return {root,steer,fs,rs,cs,hands}}
function buildBike(){const root=new THREE.Group(),roll=new THREE.Group();root.add(roll);const rig=MODEL?rigModel():procRig();roll.add(rig.root);return {root,roll,rig}}
// =====================================================================================================
// THE RIDER: the procedural fly (fly.js, inlined above) on the bike. Two functions, nothing else touches him:
//   buildRider(G) -> THREE.Object3D   builds him in the roll frame (origin rear contact, x forward, y up, z rider's right, metres).
//       G: {R wheel radius, RH rear hub, FH front hub, BB bottom bracket, SAD saddle top, HT head-tube top, HB head-tube bottom,
//           HOOD hood top (x,y), hoodZ half hood spacing, crankLen, crank0 drive-side crank angle at crankAngle 0} (THREE.Vector3 / numbers).
//       The object is added to bike.roll, so it leans and yaws with the bike; the fly is ~1.3 m long (RP.scale x a 1 m body).
//   poseRider(rider, s, crankAngle, hoods, roll)   called every frame after the bike is posed.
//       s: [x, y, psi, v, phi, delta, steer, power, gust] (m, m, rad, m/s, rad, rad, Nm, W, Nm); crankAngle: rad, the drive-side crank
//       points at angle G.crank0 + crankAngle in the x-y plane (it decreases as the bike rolls forward: clockwise seen from the right);
//       hoods: [left, right] THREE.Vector3 hood positions in the roll frame (they move with the steering); roll: the lean actually shown
//       (= phi while riding, the tip-over angle after a fall).
// Pose: body over the frame (head above the stem, abdomen over the saddle), pitched down toward the bars; front feet on the hoods,
// middle feet on the down tube, hind feet on pedals that follow the crank arms (the GLB has no pedals, so the rider carries two);
// wings folded, spreading for half a second whenever |lean| > 8 deg (flight reflex); head counter-rolls; halteres and antennae
// swing with the roll rate; the body counter-leans a little. FB.RP holds the tunables, FB.setRider swaps him.
// =====================================================================================================
const RP={scale:1.3,dx:0.11,dy:0.175,pitch:10,droop:0.38,midU:0.5,midZ:0.055,midUp:0.025,pedalZ:0.13,counter:0.12,headK:0.6,jiggle:0.25,flare:12};
const _X=V(1,0,0),_qj=new THREE.Quaternion(),_bq=new THREE.Quaternion(),_bu=new THREE.Vector3();
function buildRider(G){const rig=new THREE.Group();rig.name='rider';const fly=makeFly({srgb:true});fly.root.scale.setScalar(RP.scale);rig.add(fly.root);
 fly.root.traverse(o=>{if(o.isMesh&&o.material!==fly.materials.wing)o.castShadow=true});
 const dark=flat(0x26272b),pedals=[];
 for(const s of[-1,1]){const p=new THREE.Group();const plate=new THREE.Mesh(new THREE.BoxGeometry(0.095,0.016,0.065),dark);plate.castShadow=true;p.add(plate);
  const sp=new THREE.Mesh(new THREE.CylinderGeometry(0.007,0.007,0.07,6),dark);sp.rotation.x=Math.PI/2;sp.position.z=-s*0.035;p.add(sp);rig.add(p);pedals.push(p)}
 rig.userData={fly,G,pedals,w:0,hold:0,rate:0,prevRoll:0,prevT:0,bail:false,bailRoll:0,bailPos:V(0,0),wingMode:0,feet:[0,1,2,3,4,5].map(()=>V(0,0)),
  poles:[V(0.6,0.5,-1),V(0.6,0.5,1),V(0.25,0.35,-1),V(0.25,0.35,1),V(0.8,0.6,-0.7),V(0.8,0.6,0.7)],body:{pos:V(0,0),pitch:0,roll:0,quaternion:null}};
 return rig}
function poseRider(rider,s,crankAngle,hoods,roll){const U=rider.userData,{fly,G}=U,now=performance.now()/1000;roll=roll||0;
 const dt=U.prevT?Math.min(0.1,Math.max(1e-3,now-U.prevT)):0.016;U.prevT=now;
 const rr=Math.max(-4,Math.min(4,(roll-U.prevRoll)/dt));U.prevRoll=roll;U.rate+=(rr-U.rate)*(1-Math.exp(-dt/0.06));
 const bail=!!U.bail,wm=U.wingMode||0;                                                   // bail: standing on the ground beside the bike; wingMode: page override (+1 out, -1 folded)
 if(!bail&&Math.abs(roll)>RP.flare*Math.PI/180)U.hold=0.6;else U.hold=Math.max(0,U.hold-dt);   // flight reflex: wings out for a moment when the lean gets big
 const wt=wm>0?1:wm<0?0:(U.hold>0?1:0);U.w+=(wt-U.w)*(1-Math.exp(-dt/(wt>U.w?0.08:wm<0?0.22:0.35)));
 const F=U.feet;F[0].copy(hoods[0]);F[1].copy(hoods[1]);
 const mx=G.HB.x+(G.BB.x-G.HB.x)*RP.midU,my=G.HB.y+(G.BB.y-G.HB.y)*RP.midU+RP.midUp;F[2].set(mx,my,-RP.midZ);F[3].set(mx,my,RP.midZ);
 for(const k of[0,1]){const sg=k?1:-1,a=G.crank0+crankAngle+(k?0:Math.PI),p=U.pedals[k];
  p.position.set(G.BB.x+G.crankLen*Math.cos(a),G.BB.y+G.crankLen*Math.sin(a),sg*RP.pedalZ);F[4+k].copy(p.position);F[4+k].y+=0.012}
 const B=U.body;
 if(bail){_bq.setFromAxisAngle(_X,-U.bailRoll);B.quaternion=_bq;B.pos.copy(U.bailPos).add(_bu.set(0,fly.standHeight*RP.scale,0)).applyQuaternion(_bq)}   // upright on six feet at bailPos (bike frame), undoing the bike's roll
 else{B.quaternion=null;B.pos.set(G.SAD.x+RP.dx,G.SAD.y+RP.dy,0);B.pitch=RP.pitch*Math.PI/180;B.roll=-RP.counter*roll}
 poseFly(fly,{feet:bail?null:F,poles:bail?null:U.poles,body:B,wings:U.w,abdomen:bail?0.18:RP.droop,t:now});
 fly.head.rotation.x=bail?0:Math.max(-0.6,Math.min(0.6,-RP.headK*roll));                       // gaze stabilisation: the head stays more level than the bike
 const j=Math.max(-0.5,Math.min(0.5,RP.jiggle*U.rate));                                 // roll rate -> halteres and antennae lag behind
 for(let i=0;i<2;i++){fly.halteres[i].quaternion.premultiply(_qj.setFromAxisAngle(_X,-j));fly.antennae[i].rotation.x=-0.8*j}}
let makeRider=buildRider,poseRiderFn=poseRider;
function poseBike(s,roll){const [x,y,psi,,,delta]=s;bike.root.position.set(x,0,y);bike.root.rotation.y=-psi;bike.roll.rotation.x=roll;
 const wa=x/G.R,ca=-wa/1.5;  // wheels and crank turn clockwise seen from the drive side; 1.5 gear ratio
 bike.rig.steer.rotation.y=-delta;spin(bike.rig.fs,-wa);spin(bike.rig.rs,-wa);spin(bike.rig.cs,ca);bike.root.updateMatrixWorld(true);
 const hoods=bike.rig.hands.map(h=>{h.getWorldPosition(_w);return bike.roll.worldToLocal(_w.clone())});
 if(rider)poseRiderFn(rider,s,ca,hoods,roll)}
// =====================================================================================================
// the brain panel: the same point cloud as the dashboard, rest dim blue, firing orange/white, slow sway; per neuron when the attempt was recorded
// =====================================================================================================
const REST=[0.016,0.021,0.038],HOT=[1,0.55,0.12],PEAK=[1,0.97,0.85],DIM=[0.03,0.045,0.09];let bm=null;
async function initBrain(){const c=$('bc');if(typeof DecompressionStream==='undefined')return;
 const r=await fetch('data/cloud.bin');if(!r.ok)throw new Error('cloud.bin '+r.status);const u=await inflate(r);
 const nP=META.cloud.points,lo=META.cloud.lo,hi=META.cloud.hi,qq=new Uint16Array(u.buffer,0,nP*3),reg=new Uint8Array(u.buffer,nP*6,nP),xyz=new Float32Array(nP*3);
 // cloud axes: x left-right, y ventral, z from the brain down the nerve cord -> show the CNS lying along x, dorsal side up
 for(let p=0,p3=0;p<nP;p++,p3+=3){const dq=a=>lo[a]+qq[p3+a]/65535*(hi[a]-lo[a]);xyz[p3]=dq(2);xyz[p3+1]=-dq(1);xyz[p3+2]=dq(0)}
 const rr=new THREE.WebGLRenderer({canvas:c,antialias:false});rr.setPixelRatio(Math.min(devicePixelRatio,2));
 const sc=new THREE.Scene();sc.background=new THREE.Color(0x0d1017);const cam=new THREE.PerspectiveCamera(30,1,0.05,20);
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(xyz,3));const col=new Float32Array(nP*3);g.setAttribute('color',new THREE.BufferAttribute(col,3));
 sc.add(new THREE.Points(g,new THREE.PointsMaterial({size:0.015,vertexColors:true,transparent:true,opacity:0.85,blending:THREE.AdditiveBlending,depthWrite:false})));
 bm={rr,sc,cam,g,col,reg,nP,rotY:0,rotX:0.6,drag:false,px:0,py:0,key:'',ph:0};
 c.addEventListener('pointerdown',e=>{bm.drag=true;bm.px=e.clientX;bm.py=e.clientY;c.setPointerCapture(e.pointerId)});
 c.addEventListener('pointermove',e=>{if(!bm.drag)return;bm.rotY+=(e.clientX-bm.px)*0.008;bm.rotX=Math.max(-1.4,Math.min(1.4,bm.rotX+(e.clientY-bm.py)*0.008));bm.px=e.clientX;bm.py=e.clientY});
 c.addEventListener('pointerup',()=>bm.drag=false);
 const rs=()=>{const w=c.clientWidth,h=c.clientHeight;if(!w||!h)return;rr.setSize(w,h,false);cam.aspect=w/h;cam.updateProjectionMatrix()};new ResizeObserver(rs).observe(c);rs()}
function paintBrain(t){if(!bm)return;const a=ST.att,act=ST.act,has=!!(a&&act&&ST.actId===a.id);let key='none',i=0,j=0,al=0,nB=0;
 if(has){nB=act.length/bm.nP|0;const f=t*1000/META.binMs-0.5;i=Math.max(0,Math.min(nB-1,Math.floor(f)));j=Math.min(nB-1,i+1);al=Math.max(0,Math.min(1,f-i));key=a.id+':'+i+':'+al.toFixed(2)}
 if(key!==bm.key){bm.key=key;const col=bm.col,nP=bm.nP;
  if(!has){for(let k=0;k<nP*3;k+=3){col[k]=DIM[0];col[k+1]=DIM[1];col[k+2]=DIM[2]}}
  else{const o1=i*nP,o2=j*nP;for(let p=0,k=0;p<nP;p++,k+=3){const v=(act[o1+p]*(1-al)+act[o2+p]*al)/255,g=v<0.5?v*2:1,h=v<0.5?0:(v-0.5)*2;
   col[k]=REST[0]+(HOT[0]-REST[0])*g+(PEAK[0]-HOT[0])*h;col[k+1]=REST[1]+(HOT[1]-REST[1])*g+(PEAK[1]-HOT[1])*h;col[k+2]=REST[2]+(HOT[2]-REST[2])*g+(PEAK[2]-HOT[2])*h}}
  bm.g.attributes.color.needsUpdate=true}
 if(!bm.drag)bm.ph+=0.005;const ry=bm.rotY+0.5*Math.sin(bm.ph),d=3.3;
 bm.cam.position.set(d*Math.sin(ry)*Math.cos(bm.rotX),d*Math.sin(bm.rotX),d*Math.cos(ry)*Math.cos(bm.rotX));bm.cam.lookAt(0,0,0);bm.rr.render(bm.sc,bm.cam)}
// =====================================================================================================
// the montage: attempts in id order; significant ones are played, the others flipped through at 25/s; one rider on the road at a time
// =====================================================================================================
const CAMS=['side','chase','quarter'],VIEWS={side:{off:V(0.5,1.2,3.9),tgt:V(0.3,0.72,0)},quarter:{off:V(1.55,1.25,5.2),tgt:V(0.3,0.7,0)}};
const ST={cur:-1,att:null,phase:'idle',tA:0,tE:0,tC:0,flipAcc:0,flipN:0,playing:true,speed:1,sig:Q.get('sig')!=='0',cam:CAMS.includes(Q.get('cam'))?Q.get('cam'):'side',
 T:null,rows:null,played:null,evs:[],act:null,actId:-1,brainState:'none',token:0,snap:true,camFrozen:false,ready:false};
function stateAt(t){const T=ST.T,R=ST.rows,n=R.length;if(n===1)return R[0];
 let k=Math.min(n-1,Math.max(0,Math.floor(t/0.05)));while(k>0&&T[k]>t)k--;while(k<n-1&&T[k+1]<=t)k++;
 if(k>=n-1)return R[n-1];const a=Math.max(0,Math.min(1,(t-T[k])/(T[k+1]-T[k]))),A=R[k],B=R[k+1],o=new Array(9);for(let i=0;i<9;i++)o[i]=A[i]+(B[i]-A[i])*a;return o}
function deriveEvents(T,rows,a,prevBest){const ev=[],push=(t,k,arg)=>ev.push({t,k,arg});
 push(0,'climb');if(rows.length>1)push(T[1],'pedal');
 let mark=5,gustArmed=true,gustT=-9,leanSide=0,drift=0,rec=false,up5=false,up10=false;
 for(let i=0;i<rows.length;i++){const t=T[i];if(t>a.t+1e-6)break;const r=rows[i],x=r[0],y=r[1],phi=r[4]*57.2958,g=r[8];
  while(x>=mark){push(t,'mark',mark);mark+=5}
  if(gustArmed){if(Math.abs(g)>3&&t-gustT>1.5){push(t,g>0?'gustL':'gustR');gustArmed=false;gustT=t}}else if(Math.abs(g)<1.5)gustArmed=true;
  if(leanSide===0){if(Math.abs(phi)>4)leanSide=phi>0?1:-1}else if(Math.abs(phi)<2){push(t,leanSide>0?'wobR':'wobL');leanSide=0}
  if(drift===0){if(Math.abs(y)>1.5){drift=y>0?1:-1;push(t,drift>0?'driftR':'driftL')}}else if(Math.abs(y)<0.7){push(t,'centre');drift=0}
  if(!rec&&prevBest>0&&x>prevBest){push(t,'record');rec=true}
  if(!up5&&t>=5){push(t,'up');up5=true}if(!up10&&t>=10){push(t,'up');up10=true}}
 push(a.t,['fin','fell','off','bail'][a.o]||'fell');return ev}
const endDur=o=>o===2?1.5:o===0?0.7:1.3,TIP=1.2;let bikeLow0=0;   // a fall tips bike and rider 69 deg to the lean side (bar end, pedal and his legs prop them up)
const _bx=new THREE.Box3();
function lowestY(o,skip){if(skip&&skip.indexOf(o)>=0)return Infinity;let m=Infinity;const g=o.geometry;   // lowest world y of an object tree (bbox corners)
 if(g){if(!g.boundingBox)g.computeBoundingBox();_bx.copy(g.boundingBox).applyMatrix4(o.matrixWorld);m=_bx.min.y}
 for(const c of o.children){const v=lowestY(c,skip);if(v<m)m=v}return m}
let hintKey='';function hint(k){if(k===hintKey)return;hintKey=k;const h=$('hint');if(!k)h.classList.add('hide');else{h.classList.remove('hide');h.textContent=tt(k)}}
function nextSig(i,dir){const n=ATT.length;for(let s=1;s<=n;s++){const j=((i+dir*s)%n+n)%n;if(!ST.sig||SIG.has(j))return j}return i}
async function goTo(i){const n=ATT.length;if(!n)return;i=((i%n)+n)%n;const a=ATT[i],tok=++ST.token;
 Object.assign(ST,{cur:i,att:a,phase:'load',tA:0,tE:0,tC:0,rows:null,played:null,evs:[],snap:true,camFrozen:false,act:null,actId:-1,brainState:a.b?'loading':'none'});
 logKey='';drawTimeline();
 if(a.b)loadBrainBin(a.id).then(u=>{if(tok===ST.token){ST.act=u;ST.actId=a.id;ST.brainState='own'}}).catch(e=>{console.warn(e);if(tok===ST.token)ST.brainState='none'});
 try{const gen=await loadGen(a.gen);if(tok!==ST.token)return;const rr=gen.riders[a.rider];
  ST.T=gen.t;ST.rows=rr.rows;ST.played=a;ST.evs=deriveEvents(gen.t,rr.rows,a,BB[i]);ST.phase='ride';ST.tA=0}
 catch(e){console.warn('attempt '+a.id+' failed to load',e);if(tok===ST.token){ST.phase='card';ST.tC=0}}
 const nx=nextSig(i,1);if(nx!==i&&ATT[nx].gen!==a.gen)loadGen(ATT[nx].gen).catch(()=>{})}  // prefetch the next generation
function advance(){const n=ATT.length,nx=ST.cur+1>=n?0:ST.cur+1;
 if(ST.sig&&!SIG.has(nx)){let c=0,j=nx;while(!SIG.has(j)){c++;j=(j+1)%n;if(c>n)break}ST.flipN=c;ST.phase='flip';ST.flipAcc=0;ST.att=ATT[nx];ST.cur=nx;tick();drawTimeline()}
 else goTo(nx)}
function tick(){const t=$('atitle');t.classList.remove('tick');void t.offsetWidth;t.classList.add('tick')}
function step(dt){const a=ST.att;if(!a)return;
 switch(ST.phase){
  case 'ride':ST.tA+=dt*ST.speed;if(ST.tA>=a.t){ST.tA=a.t;ST.phase='end';ST.tE=0}break;
  case 'end':ST.tE+=dt*ST.speed;if(ST.tE>=endDur(a.o)){ST.phase='card';ST.tC=0}break;
  case 'card':ST.tC+=dt;if(ST.tC>=1.1)advance();break;
  case 'flip':ST.flipAcc+=dt;while(ST.flipAcc>=0.04){ST.flipAcc-=0.04;const nx=(ST.cur+1)%ATT.length;if(!ST.sig||SIG.has(nx)){goTo(nx);break}ST.cur=nx;ST.att=ATT[nx];ST.flipN--;tick();drawTimeline()}break}}
// ---------- camera: side view from the rider's right (drive side), low and close like the reference, following with a lerp; or a chase cam or a three-quarter view
const camPos=V(5.4,1.6,1.6),camTgt=V(0,0.8,0),camDes=V(0,0,0),tgtDes=V(0,0,0);
function updateCam(s,dt){if(s){const base=V(s[0],0,s[1]),frozen=ST.camFrozen;  // frozen (off the road): the camera stays put and only pans after him
  if(ST.view){if(!frozen)camDes.copy(base).add(ST.view.off);tgtDes.copy(base).add(ST.view.tgt)}
  else if(ST.cam==='chase'){const yaw=-s[2],fwd=V(Math.cos(yaw),0,-Math.sin(yaw)),right=V(Math.sin(yaw),0,Math.cos(yaw));
   if(!frozen)camDes.copy(base).addScaledVector(fwd,-5.2).addScaledVector(right,1.4).add(V(0,1.9,0));tgtDes.copy(base).add(V(0,0.9,0)).addScaledVector(fwd,frozen?0:1.5)}
  else{const v=VIEWS[ST.cam]||VIEWS.side;if(!frozen)camDes.copy(base).add(v.off);tgtDes.copy(base).add(V(frozen?0:v.tgt.x,v.tgt.y,v.tgt.z))}}
 const snap=ST.snap&&!!s,k=snap?1:1-Math.exp(-dt/0.22);camPos.lerp(camDes,k);camTgt.lerp(tgtDes,snap?1:1-Math.exp(-dt/0.14));camera.position.copy(camPos);camera.lookAt(camTgt);if(s)ST.snap=false;
 if(s){sun.position.set(s[0]-5,15,7);sun.target.position.set(s[0],0,0)}}
// ---------- one frame: pose, camera, panel, brain, render
let lastTs=0,logKey='',done=false;
function draw(dt){const a=ST.att;let s=null;
 if(bike&&ST.rows&&ST.played){const p=ST.played,ph=ST.phase,U=rider?rider.userData:null;let roll=0,lift=false;
  if(U){U.bail=false;U.wingMode=0}
  if(ph==='ride'){s=stateAt(ST.tA);roll=s[4]}
  else{const e=stateAt(p.t),tE=ph==='end'?ST.tE:99;s=e.slice();
   if(p.o===2){const u=Math.min(tE,1.5);s[0]=e[0]+e[3]*Math.cos(e[2])*u;s[1]=e[1]+e[3]*Math.sin(e[2])*u;roll=e[4];ST.camFrozen=true}   // rolls on into the grey, camera stays
   else if(p.o===1||p.o===3){const sg=e[4]>=0?1:-1,u=ease(Math.min(1,tE/0.6));roll=e[4]+(sg*TIP-e[4])*u;                                    // tips over to the lean side
    if(p.o===1){lift=true;if(U)U.wingMode=tE<0.2?1:-1}                                                                                      // startle, then the wings fold as he lies there
    else if(U){const h=Math.min(tE,0.7)/0.7;U.bail=true;U.bailRoll=roll;U.bailPos.set(0.35*h,0.55*Math.sin(Math.PI*h),-sg*1.7*h);U.wingMode=h<1?1:-1}}   // hops off to the other side, lands on six feet
   else{const u=Math.min(tE,0.7);s[0]=e[0]+e[3]*Math.cos(e[2])*u*0.6;s[1]=e[1]+e[3]*Math.sin(e[2])*u*0.6;roll=e[4]}}
  poseBike(s,roll);
  if(lift){const low=Math.min(lowestY(bike.rig.root)-bikeLow0,U?lowestY(rider,U.fly.wings):Infinity);if(low<0){bike.root.position.y=-low;bike.root.updateMatrixWorld(true)}}}   // a fallen rider rests on the ground, not through it
 updateCam(s,dt);
 hint(!ST.ready?'loadingBike':!ATT.length?'noData':ST.phase==='load'?'loading':'');
 refreshPanel();paintBrain(ST.phase==='ride'?ST.tA:(a?a.t:0));renderer.render(scene,camera);
 if(!done&&ST.phase==='ride'&&bike){done=true;window.DONE=1}}
function refreshPanel(){const a=ST.att;if(!a)return;const ph=ST.phase,riding=ph==='ride',live=riding&&ST.rows?stateAt(ST.tA)[0]:0;
 setT('atitle',tt('attempt',a.id));setT('genline',tt('genline',a.gen,a.rider));
 const dist=riding?live:(ph==='load'?0:a.d),t=riding?ST.tA:(ph==='load'?0:a.t);
 setT('v-dist',fmtD(dist));setT('v-best',fmtD(Math.max(BB[ST.cur]||0,dist)));setT('v-time',fmtT(t));
 const card=$('card');if(ph==='card'){card.classList.remove('hide');card.textContent=tt('card',a.id,a.o,a.t,a.d)}
 else if(ph==='flip'){card.classList.remove('hide');card.textContent=tt('skip',Math.max(1,ST.flipN))}else card.classList.add('hide');
 const ended=ph==='end'||ph==='card'||ph==='flip',endKey=['fin','fell','off','bail'][a.o]||'fell';
 setT('status',ph==='flip'?tt(endKey):ended?tt(endKey):riding?(ST.tA<0.06?tt('climb'):tt('riding')):tt('loading'));
 const tl=riding?ST.tA:(ph==='load'||ph==='flip'?-1:a.t+1);let cnt=0;for(const e of ST.evs){if(e.t<=tl)cnt++;else break}
 const key=LANG+':'+ST.cur+':'+cnt+':'+ph;if(key!==logKey){logKey=key;const L=$('log');
  if(ph==='flip'||ph==='load'){L.innerHTML=''}else{const vis=ST.evs.slice(0,cnt).reverse().slice(0,12);L.innerHTML=vis.map(e=>'<div class="ev"><div class="ts">'+fmtT(e.t)+'</div><div class="tx">'+tt(e.k,e.arg)+'</div></div>').join('')}}
 const bn=$('bnote'),bs=ST.brainState,bkey=LANG+':'+bs+':'+(ST.actId===a.id);if(bn.dataset.k!==bkey){bn.dataset.k=bkey;bn.textContent=tt(bs==='own'&&ST.actId===a.id?'rec':bs==='loading'?'loadingRec':'noRec')}}
function setT(id,v){const el=$(id);if(el.textContent!==v)el.textContent=v}
function loop(ts){const dt=Math.min(0.1,lastTs?(ts-lastTs)/1000:0);lastTs=ts;if(ST.playing&&ST.ready)step(dt);draw(dt);requestAnimationFrame(loop)}
// ---------- timeline: one thin bar per attempt, height = distance, colour by outcome, records dotted; hover for details, click to jump
function drawTimeline(){const c=$('tlc'),w=c.clientWidth,h=c.clientHeight;if(!w||!h)return;const dpr=Math.min(2,devicePixelRatio||1);if(c.width!==Math.round(w*dpr)||c.height!==Math.round(h*dpr)){c.width=Math.round(w*dpr);c.height=Math.round(h*dpr)}
 const x=c.getContext('2d');x.setTransform(dpr,0,0,dpr,0,0);x.clearRect(0,0,w,h);const n=ATT.length;if(!n)return;const bw=w/n;
 const R=META?META.riders:48,gw=bw*R;x.globalAlpha=1;x.fillStyle='#2a2e36';x.font='8px '+getComputedStyle(document.body).fontFamily;x.textBaseline='top';
 for(let i=0;i<n;i+=R){x.fillStyle='#2a2e36';x.fillRect(Math.round(i*bw),0,1,h);if(gw>=22){x.fillStyle='#6f747c';x.fillText(String(ATT[i].gen),i*bw+3,1)}}   // one tick per generation
 for(let i=0;i<n;i++){const a=ATT[i],bh=Math.max(1.5,(h-9)*a.d/DMAX);x.globalAlpha=(ST.sig&&!SIG.has(i))?0.3:0.9;x.fillStyle=COL[a.o]||COL[1];x.fillRect(i*bw,h-bh,Math.max(0.8,bw-0.4),bh)}
 x.globalAlpha=1;x.fillStyle='#fff';for(let i=0;i<n;i++){const a=ATT[i];if(a.r)x.fillRect(i*bw+bw/2-1,h-Math.max(1.5,(h-9)*a.d/DMAX)-4,2,2)}
 if(ST.cur>=0){x.strokeStyle='#fff';x.lineWidth=1;x.strokeRect(Math.round(ST.cur*bw)+0.5,0.5,Math.max(2,bw)-1,h-1)}}
function pickAt(clientX){const r=$('tlc').getBoundingClientRect(),n=ATT.length,u=(clientX-r.left)/r.width*n;let i=Math.max(0,Math.min(n-1,Math.floor(u)));   // the attempt under the pointer; in significant-only mode the nearest significant one
 if(ST.sig&&!SIG.has(i)){let bd=Infinity;for(const j of SIG){const d=Math.abs(j+0.5-u);if(d<bd){bd=d;i=j}}}return i}
{const tl=$('tl'),c=$('tlc'),tip=$('tip');const at=e=>pickAt(e.clientX);
 c.onmousemove=e=>{if(!ATT.length)return;const i=at(e),r=c.getBoundingClientRect();tip.classList.remove('hide');tip.textContent=tt('tip',ATT[i]);tip.style.left=Math.max(80,Math.min(r.width-80,e.clientX-r.left))+'px'};
 c.onmouseleave=()=>tip.classList.add('hide');c.onclick=e=>{if(ATT.length)goTo(at(e))};
 c.addEventListener('wheel',e=>{e.preventDefault();if(ATT.length)goTo(nextSig(ST.cur,e.deltaY>0||e.deltaX>0?1:-1))},{passive:false});new ResizeObserver(drawTimeline).observe(tl)}
// ---------- controls
function setPlaying(p){ST.playing=p;const b=$('play');b.textContent=p?'❚❚':'▶';b.title=tt(p?'pause':'play')}
function setSpeed(v){ST.speed=v;$('speed').value=String(v)}
function setSig(on){ST.sig=on;const b=$('sig');b.classList.toggle('on',on);b.textContent=tt(on?'sigOn':'sigOff');drawTimeline()}
function setCam(c){ST.cam=c;ST.snap=true;$('cam').textContent=tt(c==='chase'?'camChase':c==='quarter'?'camQuarter':'camSide')}
$('play').onclick=()=>setPlaying(!ST.playing);$('speed').onchange=e=>setSpeed(parseFloat(e.target.value));
$('prev').onclick=()=>goTo(nextSig(ST.cur,-1));$('next').onclick=()=>goTo(nextSig(ST.cur,1));
$('sig').onclick=()=>setSig(!ST.sig);$('cam').onclick=()=>setCam(CAMS[(CAMS.indexOf(ST.cam)+1)%CAMS.length]);
addEventListener('keydown',e=>{if(e.target&&/^(SELECT|INPUT|TEXTAREA)$/.test(e.target.tagName))return;
 if(e.key===' '){e.preventDefault();setPlaying(!ST.playing)}else if(e.key==='ArrowLeft')$('prev').click();else if(e.key==='ArrowRight')$('next').click();
 else if(e.key==='1'||e.key==='2'||e.key==='4')setSpeed(+e.key);else if(e.key==='5')setSpeed(0.5);
 else if(e.key==='['||e.key===']'){const sp=[0.5,1,2,4],k=Math.max(0,Math.min(3,sp.indexOf(ST.speed)+(e.key===']'?1:-1)));setSpeed(sp[k])}
 else if(e.key==='c'||e.key==='C')$('cam').click()});
LANG_HOOKS.push(()=>{setPlaying(ST.playing);setSig(ST.sig);setCam(ST.cam);logKey='';hintKey='';if(ST.att)refreshPanel()});
applyLang();
if(Q.get('speed'))setSpeed(parseFloat(Q.get('speed'))||1);
function resize(){const w=stage.clientWidth,h=stage.clientHeight;if(!w||!h)return;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}
new ResizeObserver(resize).observe(stage);resize();
// ---------- debug / integration hooks
window.FB={ST,RP,get ATT(){return ATT},get SIG(){return SIG},goTo,advance,pickAt,setView(ox,oy,oz,tx,ty,tz){ST.view=ox===undefined?null:{off:V(ox,oy,oz),tgt:V(tx,ty,tz)};ST.snap=true},seek:t=>{if(ST.rows){ST.phase='ride';ST.tA=Math.min(t,ST.att.t);ST.camFrozen=false}},play:setPlaying,setSpeed,setSig,setCam,
 setRider(make,pose){if(rider)bike.roll.remove(rider);makeRider=make||buildRider;poseRiderFn=pose||poseRider;rider=makeRider(G);bike.roll.add(rider)}};
// ---------- boot: index.json and the embedded model in parallel, then the first attempt
let bikeReady=false,dataReady=false;
function maybeStart(){if(!bikeReady||!dataReady||ST.ready)return;ST.ready=true;
 if(!ATT.length)return;let i=0;const want=parseInt(Q.get('a'));if(want){const j=ATT.findIndex(a=>a.id===want);if(j>=0)i=j}goTo(i)}
function start(){G=MODEL?modelGeo():procGeo();bike=buildBike();scene.add(bike.root);rider=makeRider(G);bike.roll.add(rider);poseBike([0,0,0,0,0,0,0,0,0],0);
 bikeLow0=Math.min(0,lowestY(bike.rig.root));bikeReady=true;maybeStart()}   // bikeLow0: the model's bounding boxes reach a little under the tyre contact when upright
fetch('data/index.json').then(r=>r.json()).then(m=>{META=m;ATT=m.attempts||[];computeSig();drawTimeline();dataReady=true;maybeStart();
 initBrain().catch(e=>{console.warn('brain map failed',e)})}).catch(e=>{console.warn('index.json failed',e);dataReady=true;maybeStart()});
const b64=$('bikeglb').textContent.trim();
if(b64){const bin=atob(b64),buf=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)buf[i]=bin.charCodeAt(i);
 const gl=new THREE.GLTFLoader(),dl=new THREE.DRACOLoader();dl.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/libs/draco/');gl.setDRACOLoader(dl);
 gl.parse(buf.buffer,'',g=>{MODEL=g.scene;start()},e=>{console.warn('bike model failed, using the plain bike',e);start()})}
else start();
requestAnimationFrame(loop);
</script></body></html>
"""


def read_manifest(path, tries=12):
    """attempts.json, retried while the job is rewriting it."""
    for i in range(tries):
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            if i == tries - 1:
                raise
            time.sleep(0.5)


def write_atomic(path, data):
    tmp = path.with_name(path.name + ".tmp")
    if isinstance(data, str):
        tmp.write_text(data, encoding="utf-8")
    else:
        tmp.write_bytes(data)
    os.replace(tmp, path)


def load_gen(path):
    """The arrays the page needs from one gen*.npz, or None when the file cannot be read (still being written)."""
    try:
        z = np.load(path)
        out = {k: z[k] for k in ("t", "state", "steer", "power", "gust", "t_end", "distance", "outcome", "keep", "act", "point_region")}
        out["bin_ms"] = float(z["bin_ms"]) if "bin_ms" in z.files else 100.0
        out["cloud_hz"] = float(z["cloud_hz"]) if "cloud_hz" in z.files else 40.0
        return out
    except Exception as e:  # BadZipFile, KeyError, ValueError while the job is writing
        print(f"  skip {path.name}: {type(e).__name__}: {e}")
        return None


def gen_rows(z, r, n):
    s = z["state"][:n, r].astype(np.float64)
    cols = [s[:, 0].round(3), s[:, 1].round(3), s[:, 2].round(4), s[:, 3].round(3), s[:, 4].round(4), s[:, 5].round(4),
            z["steer"][:n, r].astype(np.float64).round(2), z["power"][:n, r].astype(np.float64).round(1), z["gust"][:n, r].astype(np.float64).round(2)]
    return np.column_stack(cols).tolist()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", nargs="?", default="results/attempts")
    ap.add_argument("out", nargs="?", default="results/attempts_page")
    ap.add_argument("--force", action="store_true", help="re-export generations whose json/bins already exist")
    ap.add_argument("--bike", default=str(DEFAULT_BIKE), help="GLB (Draco ok) to embed, or 'none' for the plain procedural bike")
    a = ap.parse_args()
    src, dst = ROOT / a.src, ROOT / a.out
    data, brain_dir = dst / "data", dst / "data" / "brain"
    brain_dir.mkdir(parents=True, exist_ok=True)
    man = read_manifest(src / "attempts.json")
    R, secs, bin_ms = int(man["riders"]), float(man["seconds"]), float(man.get("bin_ms", 100.0))
    regions = [str(x) for x in man["regions"]]
    zh_labels = {i: str(l) for i, l in zip(regions, man.get("labels", []))}

    xyz = np.fromfile(ROOT / "web_data" / "brain_xyz.bin", dtype=np.float32).reshape(-1, 3)
    lo, hi = xyz.min(0), xyz.max(0)
    q = np.round((xyz - lo) / (hi - lo) * 65535).astype("<u2")
    n_points = len(xyz)

    attempts, gens_done, cloud_written = [], [], (data / "cloud.bin").exists() and not a.force
    t0 = time.time()
    for ge in man.get("generations", []):
        g, f = int(ge["gen"]), src / ge["file"]
        if not f.exists():
            print(f"  gen {g}: {f.name} not there yet")
            continue
        keep = [int(k) for k in ge.get("keep", [])]
        ids = {k: g * R + k + 1 for k in range(R)}
        have = (data / f"gen{g}.json").exists() and all((brain_dir / f"{ids[k]}.bin").exists() for k in keep)
        z = None
        if a.force or not have or not cloud_written:
            z = load_gen(f)
            if z is None:
                continue
            if z["state"].shape[1] != R or len(z["t_end"]) != R:
                print(f"  skip {f.name}: {R} riders expected, {z['state'].shape[1]} found")
                continue
            t = z["t"].astype(np.float64)
            nT = len(t)
            if not cloud_written:
                reg = np.asarray(z["point_region"], dtype=np.uint8)
                if len(reg) != n_points:
                    print(f"  point_region has {len(reg)} points, cloud has {n_points}: regions zeroed")
                    reg = np.zeros(n_points, np.uint8)
                write_atomic(data / "cloud.bin", zlib.compress(q.tobytes() + reg.tobytes(), 9))
                cloud_written = True
            riders = []
            for r in range(R):
                te = float(z["t_end"][r])
                n = int(min(nT, np.searchsorted(t, te - 1e-6) + 5))  # a few frozen rows after the end
                riders.append({"n": n, "rows": gen_rows(z, r, n)})
            act = z["act"]
            for kk, r in enumerate(keep):
                if kk >= act.shape[1]:
                    break
                nb = int(min(act.shape[0], math.ceil(float(z["t_end"][r]) * 1000 / bin_ms) + 1))
                write_atomic(brain_dir / f"{ids[r]}.bin", zlib.compress(np.ascontiguousarray(act[:nb, kk, :]).tobytes(), 6))
            write_atomic(data / f"gen{g}.json", json.dumps({"gen": g, "t": t.round(3).tolist(), "riders": riders}, separators=(",", ":")))  # last: marks the gen done
        t_end = [float(v) for v in (z["t_end"] if z is not None else ge["t_end"])]
        dist = [float(v) for v in (z["distance"] if z is not None else ge["distance"])]
        outc = [int(v) for v in (z["outcome"] if z is not None else ge["outcome"])]
        gj = None
        for r in range(R):
            if outc[r] == 0 and t_end[r] < secs - 0.06:  # see the docstring: a fall the log never caught
                if z is not None:
                    y_end = float(z["state"][int(np.searchsorted(z["t"], t_end[r] - 1e-6)), r, 1])
                else:
                    gj = gj or json.loads((data / f"gen{g}.json").read_text())
                    k = int(np.searchsorted(np.asarray(gj["t"]), t_end[r] - 1e-6))
                    y_end = float(gj["riders"][r]["rows"][min(k, gj["riders"][r]["n"] - 1)][1])
                outc[r] = 2 if abs(y_end) > 3.3 else 1
            attempts.append({"id": ids[r], "gen": g, "rider": r, "t": round(t_end[r], 2), "d": round(dist[r], 2), "o": outc[r],
                             "b": 1 if r in keep else 0, "r": 0})
        gens_done.append(g)
        print(f"  gen {g}: {'exported' if z is not None else 'kept'} ({time.time() - t0:.0f} s)")
    attempts.sort(key=lambda at: at["id"])
    gens_done.sort()
    best = attempts[0]["d"] if attempts else 0.0   # records in attempt order: further than every attempt before (the first one is the baseline)
    for at in attempts[1:]:
        if at["d"] > best:
            best, at["r"] = at["d"], 1
    index = {"neurons": NEURONS, "synapses": SYNAPSES, "riders": R, "seconds": secs, "binMs": bin_ms, "cloudHz": 40.0,
             "generations": gens_done, "regions": [{"id": i, "en": REG_EN.get(i, i), "zh": zh_labels.get(i, REG_ZH.get(i, i))} for i in regions],
             "cloud": {"points": n_points, "lo": lo.round(6).tolist(), "hi": hi.round(6).tolist()},
             "built": time.strftime("%Y-%m-%dT%H:%M:%S"), "attempts": attempts}
    write_atomic(data / "index.json", json.dumps(index, separators=(",", ":")))
    bike = "" if a.bike == "none" or not Path(a.bike).exists() else base64.b64encode(Path(a.bike).read_bytes()).decode()
    write_atomic(dst / "index.html", HTML.replace("__BIKE__", bike))
    n_brain = sum(at["b"] for at in attempts)
    print(f"{dst}: {len(attempts)} attempts in {len(gens_done)} generations, {n_brain} with whole-brain recordings, "
          f"index.html {(dst / 'index.html').stat().st_size / 1e6:.1f} MB (bike: {Path(a.bike).name if bike else 'procedural'})")


if __name__ == "__main__":
    main()
