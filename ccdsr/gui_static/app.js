"use strict";
// Page logic of the interactive explorer. All numbers come from the Python simulator through
// /api/describe, /api/run and /api/run2d; nothing is computed here except how to draw them.

const $ = (id) => document.getElementById(id);
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, v);
  }
  node.append(...children);
  return node;
};
const clone = (value) => JSON.parse(JSON.stringify(value));
const fmt = (v, digits = 4) => (v === null || v === undefined || !isFinite(v)) ? "" : String(Number(Number(v).toPrecision(digits)));
const thousands = (v, places = 0) => Number(v).toLocaleString("en-US", { minimumFractionDigits: places, maximumFractionDigits: places });

let info = null;          // what /api/describe returned
let state = null;         // the current one-dimensional request
let state2 = null;        // the current two-dimensional request
let last = null;          // the last good one-dimensional answer
let methodOptions = {};   // options of every method, kept while it is unticked
const view = { x0: null, x1: null };   // window of the surface plot, micrometres
const syncers = [];       // functions that copy the state into the controls

// ------------------------------------------------------------ talking to Python

async function post(url, body) {
  const answer = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  return answer.json();
}

function makeRunner(url, request, show, status) {
  let busy = false, dirty = false, timer = null;
  async function go() {
    if (busy) { dirty = true; return; }
    busy = true; dirty = false;
    status.classList.remove("bad");
    status.textContent = "Working…";
    const started = performance.now();
    try {
      const out = await post(url, request());
      if (out.ok) {
        show(out);
        status.textContent = `Updated in ${((performance.now() - started) / 1000).toFixed(2)} s.`;
      } else {
        status.classList.add("bad");
        status.textContent = `These settings cannot be run: ${out.error}. The pictures below still show the last settings that worked.`;
      }
    } catch (problem) {
      status.classList.add("bad");
      status.textContent = "The simulator is not answering. Check that python -m ccdsr.gui is still running, then change any setting.";
    }
    busy = false;
    if (dirty) go();
  }
  return () => { clearTimeout(timer); timer = setTimeout(go, 40); };
}

function saveToAddress() {
  const tab = $("view-2d").hidden ? "1d" : "2d";
  try { history.replaceState(null, "", "#" + encodeURIComponent(JSON.stringify({ tab, s: state, s2: state2 }))); } catch (e) { /* too long: skip */ }
}

function loadFromAddress() {
  if (location.hash.length < 3) return null;
  try { return JSON.parse(decodeURIComponent(location.hash.slice(1))); } catch (e) { return null; }
}

// ------------------------------------------------------------------- controls

function getKey(target, key) { return key.split(".").reduce((o, k) => (o === undefined || o === null) ? undefined : o[k], target); }
function setKey(target, key, value) {
  const parts = key.split(".");
  const name = parts.pop();
  parts.reduce((o, k) => o[k], target)[name] = value;
}

function buildControl(def, target, changed) {
  const get = () => getKey(target(), def.key);
  const set = (v) => { setKey(target(), def.key, v); changed(def.key); };
  const box = el("div", { class: "ctl", "data-key": def.key });
  const name = el("span", { class: "name", text: def.label });
  const id = "c-" + def.key.replace(/\W/g, "-") + (target() === state2 ? "-2d" : "");
  if (def.scale === "choice") {
    const select = el("select", { id, "aria-label": def.label });
    for (const choice of info.choices[def.key]) select.append(el("option", { value: choice, text: choice }));
    select.addEventListener("change", () => set(select.value));
    syncers.push(() => { select.value = get(); });
    box.append(el("div", { class: "top" }, name), select);
  } else if (def.scale === "bool") {
    const check = el("input", { type: "checkbox", id });
    check.addEventListener("change", () => set(check.checked));
    syncers.push(() => { check.checked = !!get(); });
    box.append(el("label", { class: "top" }, name, check));
  } else if (def.scale === "code") {
    const text = el("input", { type: "text", id, placeholder: "empty: light simply on", "aria-label": def.label });
    text.addEventListener("change", () => {
      const cleaned = text.value.split(/[\s,]+/).filter((t) => t !== "").map(Number);
      set(cleaned.length ? cleaned : null);
    });
    syncers.push(() => { const v = get(); text.value = v ? v.join(",") : ""; });
    box.append(el("div", { class: "top" }, name), text);
  } else {
    const number = el("input", { type: "number", id, step: "any", "aria-label": def.label });
    const log = def.scale === "log";
    const range = el("input", log ? { type: "range", min: 0, max: 1000, step: 1 } : { type: "range", min: def.min, max: def.max, step: def.step });
    range.setAttribute("aria-label", def.label + " (slider)");
    const toSlider = (v) => log ? 1000 * Math.log(Math.max(v, def.min) / def.min) / Math.log(def.max / def.min) : v;
    const fromSlider = (t) => log ? Number((def.min * Math.pow(def.max / def.min, t / 1000)).toPrecision(3)) : Number(t);
    range.addEventListener("input", () => { const v = fromSlider(range.value); number.value = fmt(v, 6); set(v); });
    number.addEventListener("change", () => { const v = Number(number.value); if (number.value !== "" && isFinite(v)) { range.value = toSlider(v); set(v); } });
    syncers.push(() => { const v = get(); number.value = fmt(v, 6); range.value = toSlider(v); });
    box.append(el("div", { class: "top" }, name, el("span", { class: "val" }, number, el("span", { text: def.unit }))), range);
  }
  box.append(el("p", { class: "help", text: def.help }));
  return box;
}

function buildMethods() {
  const holder = $("methods");
  info.methods.forEach((method, index) => {
    methodOptions[method.name] = clone(method.options);
    const check = el("input", { type: "checkbox", id: "m-" + method.name });
    const chip = el("span", { class: "chip", style: `background: var(--m${index % 6})` });
    const opts = el("div", { class: "opts" });
    for (const option of Object.keys(method.options)) {
      const input = el("input", { type: "number", step: "any", id: `o-${method.name}-${option}` });
      input.addEventListener("change", () => {
        if (input.value === "" || !isFinite(Number(input.value))) return;
        methodOptions[method.name][option] = Number(input.value);
        collectMethods(); changed1();
      });
      opts.append(el("label", { for: input.id, text: option.replace(/_/g, " ") }), input);
    }
    const notes = [];
    if (method.needs_materials) notes.push("Is told the two materials of the surface, so it only runs on two-material surfaces.");
    if (method.solves_positions) notes.push("Works out the frame positions itself, starting from what it is told.");
    const box = el("div", { class: "method" }, el("label", {}, check, chip, el("span", { text: method.label })));
    if (notes.length) box.append(el("p", { class: "note", text: notes.join(" ") }));
    if (Object.keys(method.options).length) box.append(opts);
    check.addEventListener("change", () => { collectMethods(); changed1(); });
    syncers.push(() => {
      const mine = state.methods.find((m) => m.method === method.name);
      check.checked = !!mine;
      if (mine) methodOptions[method.name] = { ...methodOptions[method.name], ...mine.options };
      opts.hidden = !mine;
      for (const option of Object.keys(method.options)) $(`o-${method.name}-${option}`).value = fmt(methodOptions[method.name][option], 6);
    });
    holder.append(box);
  });
}

function collectMethods() {
  state.methods = info.methods.filter((m) => $("m-" + m.name).checked).map((m) => ({ method: m.name, options: clone(methodOptions[m.name]) }));
}

function syncAll() { for (const sync of syncers) sync(); }

let run1 = () => {}, run2 = () => {};

function changed1(key) {
  if (key === "optics.pitch_nm" && state.optics.aperture_nm > state.optics.pitch_nm) state.optics.aperture_nm = state.optics.pitch_nm;
  syncAll();
  const collimated = state.optics.gap_model === "collimated";
  document.querySelector('[data-key="optics.wavelength_nm"]').classList.toggle("off", !collimated);
  document.querySelector('[data-key="scan.code"]').classList.toggle("off", !(state.scan.exposure_fraction > 0));
  document.querySelector('[data-key="scan.wander_frames"]').classList.toggle("off", !(state.scan.wander_px > 0));
  saveToAddress();
  run1();
}

function changed2() { syncAll(); saveToAddress(); run2(); }

// -------------------------------------------------------------------- drawing

function prepare(canvas) {
  if (!canvas.dataset.h) canvas.dataset.h = canvas.getAttribute("height");
  const ratio = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = Number(canvas.dataset.h);
  canvas.width = Math.round(w * ratio); canvas.height = Math.round(h * ratio);
  canvas.style.height = h + "px";
  const g = canvas.getContext("2d");
  g.setTransform(ratio, 0, 0, ratio, 0, 0);
  g.clearRect(0, 0, w, h);
  g.font = "11.5px " + css("--font");
  return [g, w, h];
}

function ticks(lo, hi, about) {
  const raw = (hi - lo) / about, power = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 5, 10].map((m) => m * power).find((s) => s >= raw);
  const out = [];
  for (let v = Math.ceil(lo / step - 1e-9) * step; v <= hi + step * 1e-9; v += step) out.push(Math.abs(v) < step * 1e-9 ? 0 : v);
  return out;
}

// Draws the frame, grid and labels of a plot and returns functions from data to canvas coordinates.
function axes(g, w, h, o) {
  const m = { l: 52, r: 12, t: 10, b: 36 };
  const placed = [];
  if (o.legend) {
    let x = m.l, row = 0;
    for (const item of o.legend) {
      const width = 23 + g.measureText(item.label).width + 16;
      if (x > m.l && x + width > w - m.r) { x = m.l; row += 1; }
      placed.push({ item, x, y: 12 + 16 * row });
      x += width;
    }
    m.t = 26 + 16 * row;
  }
  const pw = w - m.l - m.r, ph = h - m.t - m.b;
  const fx = o.logx ? Math.log10 : (v) => v;
  const X = (v) => m.l + pw * (fx(v) - fx(o.x0)) / (fx(o.x1) - fx(o.x0));
  const Y = (v) => m.t + ph * (1 - (v - o.y0) / (o.y1 - o.y0));
  g.strokeStyle = css("--grid"); g.fillStyle = css("--fg2"); g.lineWidth = 1;
  g.textAlign = "center"; g.textBaseline = "top";
  const xt = o.xticks || ticks(o.x0, o.x1, Math.max(3, Math.floor(pw / 90)));
  for (const v of xt) {
    if (v < Math.min(o.x0, o.x1) || v > Math.max(o.x0, o.x1)) continue;
    g.beginPath(); g.moveTo(X(v), m.t); g.lineTo(X(v), m.t + ph); g.stroke();
    g.fillText(o.xformat ? o.xformat(v) : fmt(v, 6), X(v), m.t + ph + 5);
  }
  g.textAlign = "right"; g.textBaseline = "middle";
  for (const v of ticks(o.y0, o.y1, Math.max(3, Math.floor(ph / 45)))) {
    g.beginPath(); g.moveTo(m.l, Y(v)); g.lineTo(m.l + pw, Y(v)); g.stroke();
    g.fillText(fmt(v, 6), m.l - 6, Y(v));
  }
  g.strokeStyle = css("--line"); g.strokeRect(m.l, m.t, pw, ph);
  g.textAlign = "center"; g.textBaseline = "bottom";
  g.fillText(o.xlabel, m.l + pw / 2, h - 2);
  g.save(); g.translate(11, m.t + ph / 2); g.rotate(-Math.PI / 2); g.textBaseline = "top"; g.fillText(o.ylabel, 0, -8); g.restore();
  g.textAlign = "left"; g.textBaseline = "middle";
  for (const { item, x, y } of placed) {
    g.strokeStyle = item.color; g.lineWidth = item.width || 2; g.setLineDash(item.dash || []);
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + 18, y); g.stroke(); g.setLineDash([]);
    g.fillStyle = css("--fg2"); g.fillText(item.label, x + 23, y);
  }
  return { X, Y, left: m.l, top: m.t, pw, ph, clip() { g.save(); g.beginPath(); g.rect(m.l, m.t, pw, ph); g.clip(); } };
}

function line(g, a, xs, ys, color, width = 1.5, dash = []) {
  g.strokeStyle = color; g.lineWidth = width; g.setLineDash(dash); g.lineJoin = "round";
  g.beginPath();
  let pen = false;
  for (let i = 0; i < ys.length; i++) {
    const v = ys[i];
    if (v === null || v === undefined) { pen = false; continue; }
    const x = a.X(typeof xs === "function" ? xs(i) : xs[i]), y = a.Y(v);
    if (pen) g.lineTo(x, y); else g.moveTo(x, y);
    pen = true;
  }
  g.stroke(); g.setLineDash([]);
}

const methodColor = (name) => css("--m" + (info.methods.findIndex((m) => m.name === name) % 6));

function drawSurface() {
  if (!last) return;
  const [g, w, h] = prepare($("plot-surface"));
  const dx = last.scene.dx_nm / 1000, n = last.scene.truth.length;
  if (view.x0 === null) { view.x0 = 0; view.x1 = n * dx; }
  const good = last.results.filter((r) => r.ok);
  const legend = [{ label: "true surface", color: css("--fg"), width: 2 }];
  if ($("show-seen").checked) legend.push({ label: "after the blur", color: css("--fg2"), dash: [4, 3] });
  for (const r of good) legend.push({ label: r.label, color: methodColor(r.method) });
  const a = axes(g, w, h, { x0: view.x0, x1: view.x1, y0: -0.3, y1: 1.6, xlabel: "position on the surface (µm)", ylabel: "reflectance", legend });
  const i0 = Math.max(0, Math.floor(view.x0 / dx) - 1), i1 = Math.min(n, Math.ceil(view.x1 / dx) + 1);
  const xs = (i) => (i0 + i) * dx;
  a.clip();
  if ($("show-seen").checked) line(g, a, xs, last.seen.slice(i0, i1), css("--fg2"), 1.2, [4, 3]);
  line(g, a, xs, last.scene.truth.slice(i0, i1), css("--fg"), 2);
  for (const r of good) line(g, a, xs, r.estimate.slice(i0, i1), methodColor(r.method), 1.5);
  g.restore();
}

function drawReadings() {
  if (!last) return;
  const [g, w, h] = prepare($("plot-readings"));
  const { n_frames, n_pixels, values } = last.readings;
  const a = axes(g, w, h, { x0: 0, x1: n_pixels, y0: n_frames, y1: 0, xlabel: "pixel along the sensor", ylabel: "frame number" });
  let top = 0;
  for (const v of values) if (v > top) top = v;
  const image = new ImageData(n_pixels, n_frames);
  for (let i = 0; i < values.length; i++) {
    const c = Math.max(0, Math.min(255, Math.round(255 * values[i] / (top || 1))));
    image.data[4 * i] = image.data[4 * i + 1] = image.data[4 * i + 2] = c; image.data[4 * i + 3] = 255;
  }
  const off = document.createElement("canvas"); off.width = n_pixels; off.height = n_frames;
  off.getContext("2d").putImageData(image, 0, 0);
  g.imageSmoothingEnabled = false;
  g.drawImage(off, a.left, a.top, a.pw, a.ph);
  g.strokeStyle = css("--line"); g.strokeRect(a.left, a.top, a.pw, a.ph);
}

function drawPath() {
  if (!last) return;
  const [g, w, h] = prepare($("plot-path"));
  const solved = last.results.filter((r) => r.ok && r.path_nm);
  const series = [last.path.true_nm, last.path.believed_nm, ...solved.map((r) => r.path_nm)];
  let top = 50;
  for (const s of series) for (const v of s) if (Math.abs(v) > top) top = Math.abs(v);
  top *= 1.1;
  const legend = [{ label: "true path", color: css("--fg"), width: 2 }, { label: "what the reconstruction is told", color: css("--fg2"), dash: [4, 3] }];
  for (const r of solved) legend.push({ label: "solved: " + r.label, color: methodColor(r.method) });
  const a = axes(g, w, h, { x0: 0, x1: Math.max(1, last.path.true_nm.length - 1), y0: -top, y1: top, xlabel: "frame number", ylabel: "distance from the plan (nm)", legend });
  const xs = (i) => i;
  a.clip();
  line(g, a, xs, last.path.true_nm, css("--fg"), 2);
  line(g, a, xs, last.path.believed_nm, css("--fg2"), 1.2, [4, 3]);
  for (const r of solved) line(g, a, xs, r.path_nm, methodColor(r.method), 1.5);
  g.restore();
}

function drawBlur() {
  if (!last) return;
  const [g, w, h] = prepare($("plot-blur"));
  const b = last.blur;
  const legend = [{ label: "gap", color: css("--c-gap") }, { label: "pixel opening", color: css("--c-pixel") },
    { label: "motion during the exposure", color: css("--c-motion") }, { label: "all three together", color: css("--fg"), width: 2.5 }];
  const a = axes(g, w, h, { x0: 100, x1: 20000, y0: 0, y1: 1.05, logx: true, xticks: [100, 200, 500, 1000, 2000, 5000, 10000, 20000],
    xformat: (v) => thousands(v), xlabel: "distance over which the pattern repeats (nm)", ylabel: "share that survives", legend });
  a.clip();
  g.strokeStyle = css("--fg2"); g.lineWidth = 1; g.setLineDash([2, 3]);
  for (const group of last.scene.groups) { g.beginPath(); g.moveTo(a.X(group[0]), a.top); g.lineTo(a.X(group[0]), a.top + a.ph); g.stroke(); }
  g.setLineDash([]);
  line(g, a, b.periods_nm, b.gap, css("--c-gap"));
  line(g, a, b.periods_nm, b.pixel, css("--c-pixel"));
  line(g, a, b.periods_nm, b.motion, css("--c-motion"));
  line(g, a, b.periods_nm, b.total, css("--fg"), 2.5);
  g.restore();
}

const SVG = "http://www.w3.org/2000/svg";
function svg(tag, attrs = {}, text) {
  const node = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  return node;
}

// Side view: five pixels of the sensor, the gap, and the surface beneath, with the area one reading mixes.
function drawSetup() {
  if (!last) return;
  const s = last.setup, W = 440, shown = 5;
  const scale = (W - 60) / (shown * s.pitch_nm);            // drawing units per nanometre
  const sensorTop = 34, sensorH = 26, sensorBottom = sensorTop + sensorH;
  const trueGap = s.gap_nm * scale, gap = Math.max(14, Math.min(110, trueGap));
  const surfaceY = sensorBottom + gap, x0 = 30, mid = x0 + shown * s.pitch_nm * scale / 2;
  const H = surfaceY + 104;
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Side view of the sensor above the surface" });
  const add = (tag, attrs, text) => root.append(svg(tag, attrs, text));
  // The next frame's position, drawn first so that it sits behind.
  const step = s.step_nm * scale;
  if (Math.abs(step) < W) add("rect", { x: x0 + step, y: sensorTop, width: shown * s.pitch_nm * scale, height: sensorH, style: "fill:none;stroke:var(--fg2);stroke-dasharray:4 3" });
  // The cone that one pixel collects from.
  const half = s.aperture_nm * scale / 2, spread = Math.max(s.blur_width_nm, s.aperture_nm) * scale / 2;
  add("polygon", { points: `${mid - half},${sensorBottom} ${mid + half},${sensorBottom} ${mid + spread},${surfaceY} ${mid - spread},${surfaceY}`, style: "fill:var(--accent);opacity:0.22" });
  for (let k = 0; k < shown; k++) {
    const left = x0 + k * s.pitch_nm * scale, width = s.pitch_nm * scale, open = s.aperture_nm * scale;
    add("rect", { x: left, y: sensorTop, width, height: sensorH, style: "fill:var(--pill);stroke:var(--fg2)" });
    add("rect", { x: left + (width - open) / 2, y: sensorBottom - 7, width: open, height: 7, style: "fill:var(--accent)" });
  }
  // The surface, shaded by its true reflectance, centred on the middle of the test surface.
  const dx = last.scene.dx_nm, truth = last.scene.truth, cells = Math.round(shown * s.pitch_nm / dx);
  const first = Math.max(0, Math.floor(truth.length / 2 - cells / 2));
  let start = 0;
  for (let i = 1; i <= cells; i++) {
    if (i === cells || truth[first + i] !== truth[first + start]) {
      const shade = Math.round(60 + 170 * Math.max(0, Math.min(1, truth[first + start])));
      add("rect", { x: x0 + start * dx * scale, y: surfaceY, width: (i - start) * dx * scale + 0.4, height: 16, fill: `rgb(${shade},${shade},${shade})` });
      start = i;
    }
  }
  add("rect", { x: x0, y: surfaceY, width: shown * s.pitch_nm * scale, height: 16, style: "fill:none;stroke:var(--fg2)" });
  // Labels and dimension lines.
  const dim = (xa, xb, y, label) => {
    add("line", { x1: xa, y1: y, x2: xb, y2: y, style: "stroke:var(--fg2)" });
    for (const x of [xa, xb]) add("line", { x1: x, y1: y - 4, x2: x, y2: y + 4, style: "stroke:var(--fg2)" });
    add("text", { x: (xa + xb) / 2, y: y - 6, "text-anchor": "middle" }, label);
  };
  dim(x0, x0 + s.pitch_nm * scale, sensorTop - 8, `pixel spacing ${thousands(s.pitch_nm)} nm`);
  add("line", { x1: W - 18, y1: sensorBottom, x2: W - 18, y2: surfaceY, style: "stroke:var(--fg2)" });
  add("text", { x: W - 24, y: (sensorBottom + surfaceY) / 2 + 4, "text-anchor": "end" },
    `gap ${thousands(s.gap_nm)} nm` + (Math.abs(trueGap - gap) > 1 ? " (not to scale)" : ""));
  dim(mid - spread, mid + spread, surfaceY + 34, `one reading mixes about ${thousands(Math.max(s.blur_width_nm, s.aperture_nm))} nm`);
  add("text", { x: x0, y: surfaceY + 62 }, `Blue: each pixel's opening (${thousands(s.aperture_nm)} nm) and what the middle pixel collects.`);
  add("text", { x: x0, y: surfaceY + 78 }, `Dashed: the sensor one frame later, moved ${thousands(s.step_nm)} nm.`);
  add("text", { x: x0, y: surfaceY + 94 }, "Grey strip: the surface, lighter where it reflects more. Widths to scale.");
  $("setup").replaceChildren(root);
}

function showScores() {
  const table = $("scores");
  const groups = last.scene.groups, twoMaterials = last.scene.levels !== null;
  const head = el("tr", {}, el("th", { text: "Method" }), el("th", { text: "Error against the true surface (rms, reflectance)" }));
  if (groups.length) {
    head.append(el("th", { text: "Finest bar period shown (nm)" }));
    for (const group of groups) head.append(el("th", { text: `Share of ${thousands(group[0])} nm bars` }));
  }
  if (twoMaterials) head.append(el("th", { text: "Surface given the wrong material (%)" }));
  head.append(el("th", { text: "Error of the frame positions used (nm, rms)" }), el("th", { text: "Time (s)" }));
  const rows = [head];
  const good = last.results.filter((r) => r.ok);
  const best = good.length > 1 ? Math.min(...good.map((r) => r.scores.rms_error)) : null;
  const columns = head.children.length;
  for (const r of last.results) {
    const name = el("td", {}, el("span", { class: "chip", style: `background:${methodColor(r.method)};margin-right:7px` }), r.label);
    if (!r.ok) { rows.push(el("tr", {}, name, el("td", { class: "err", colspan: columns - 1, text: "Did not run: " + r.error }))); continue; }
    if (r.note) name.append(el("div", { class: "help", text: "Warning from the solver: " + r.note }));
    const sc = r.scores, row = el("tr", {}, name);
    row.append(el("td", { class: "num" + (sc.rms_error === best ? " best" : ""), text: sc.rms_error.toFixed(3) }));
    if (groups.length) {
      row.append(el("td", { class: "num", text: sc.finest_period_nm === null ? "none" : thousands(sc.finest_period_nm) }));
      for (const share of sc.contrast_share) row.append(el("td", { class: "num", text: share === null ? "" : share.toFixed(2) }));
    }
    if (twoMaterials) row.append(el("td", { class: "num", text: sc.wrong_material_percent.toFixed(1) }));
    row.append(el("td", { class: "num", text: sc.position_error_nm === null ? "" : sc.position_error_nm.toFixed(1) }), el("td", { class: "num", text: r.seconds.toFixed(2) }));
    rows.push(row);
  }
  if (!last.results.length) rows.push(el("tr", {}, el("td", { colspan: columns, text: "No method is ticked. Tick one under Reconstruction." })));
  table.replaceChildren(...rows);
}

function showFacts() {
  $("facts").replaceChildren(...last.facts.map((f) => el("tr", {}, el("td", { text: f.label }), el("td", { text: f.value + (f.unit ? " " + f.unit : "") }))));
}

function showFile() {
  const select = $("file-method"), keep = select.value;
  const good = last.results.filter((r) => r.ok);
  select.replaceChildren(...good.map((r) => el("option", { value: r.method, text: r.label })));
  if (good.some((r) => r.method === keep)) select.value = keep;
  const chosen = good.find((r) => r.method === select.value);
  $("file").value = chosen ? chosen.file : "";
}

function showZooms() {
  const n = last.scene.truth.length, dx = last.scene.dx_nm / 1000;
  const buttons = [["Whole surface", 0, n * dx]];
  for (const group of last.scene.groups) {
    const pad = 0.15 * (group[2] - group[1]);
    buttons.push([`${thousands(group[0])} nm bars`, (group[1] - pad) * dx, (group[2] + pad) * dx]);
  }
  $("zooms").replaceChildren(...buttons.map(([label, a, b]) => {
    const button = el("button", { type: "button", text: label });
    button.addEventListener("click", () => { view.x0 = a; view.x1 = b; drawSurface(); });
    return button;
  }));
}

let shownScene = null;
function show1(out) {
  last = out;
  if (shownScene !== out.scene.name + ":" + out.scene.truth.length) { shownScene = out.scene.name + ":" + out.scene.truth.length; view.x0 = null; showZooms(); }
  showScores(); showFacts(); showFile(); drawSetup(); redraw1();
}
function redraw1() { drawSurface(); drawReadings(); drawPath(); drawBlur(); }

function surfaceInteraction() {
  const canvas = $("plot-surface");
  const span = () => canvas.clientWidth - 64;
  let drag = null;
  canvas.addEventListener("pointerdown", (e) => { drag = { x: e.clientX, x0: view.x0, x1: view.x1 }; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener("pointermove", (e) => {
    if (!drag) return;
    const shift = (drag.x - e.clientX) * (drag.x1 - drag.x0) / span();
    view.x0 = drag.x0 + shift; view.x1 = drag.x1 + shift; drawSurface();
  });
  canvas.addEventListener("pointerup", () => { drag = null; });
  canvas.addEventListener("pointercancel", () => { drag = null; });
  canvas.addEventListener("wheel", (e) => {
    if (view.x0 === null) return;
    e.preventDefault();
    const at = view.x0 + (view.x1 - view.x0) * Math.max(0, Math.min(1, (e.offsetX - 52) / span()));
    const factor = e.deltaY > 0 ? 1.25 : 0.8;
    const width = Math.max(0.2, (view.x1 - view.x0) * factor);
    const share = (at - view.x0) / (view.x1 - view.x0);
    view.x0 = at - share * width; view.x1 = view.x0 + width; drawSurface();
  }, { passive: false });
  canvas.addEventListener("dblclick", () => { view.x0 = null; drawSurface(); });
}

// ------------------------------------------------------------- two dimensions

function grey(canvas, values, width, height, top) {
  canvas.width = width; canvas.height = height;
  const image = new ImageData(width, height);
  for (let i = 0; i < values.length; i++) {
    const c = Math.max(0, Math.min(255, Math.round(255 * values[i] / top)));
    image.data[4 * i] = image.data[4 * i + 1] = image.data[4 * i + 2] = c; image.data[4 * i + 3] = 255;
  }
  canvas.getContext("2d").putImageData(image, 0, 0);
}

function show2(out) {
  const [height, width] = out.shape;
  grey($("img-truth"), out.truth, width, height, 1.25);
  grey($("img-estimate"), out.estimate, width, height, 1.25);
  let top = 1;
  for (const v of out.frame.values) if (v > top) top = v;
  grey($("img-frame"), out.frame.values, out.frame.side, out.frame.side, top);
  const facts = [
    ["Error against the true picture (rms, reflectance)", out.rms_error.toFixed(3)],
    ["Readings taken", thousands(out.readings)],
    ["Different lines across the scan that the pixels trace, per pixel spacing", thousands(out.distinct_lines_across)],
    ["Time to reconstruct", out.seconds.toFixed(2) + " s"],
  ];
  if (out.note) facts.push(["Note", out.note]);
  $("facts-2d").replaceChildren(...facts.map(([a, b]) => el("tr", {}, el("td", { text: a }), el("td", { text: b }))));
  const rows = [el("tr", {}, el("th", { text: "Line period (nm)" }), el("th", { text: "Share shown, lines varying along the scan" }), el("th", { text: "Share shown, lines varying across the scan" }))];
  const periods = [...new Set(out.groups.map((g) => g.period_nm))];
  for (const period of periods) {
    const pick = (direction) => out.groups.find((g) => g.period_nm === period && g.direction === direction);
    rows.push(el("tr", {}, el("td", { class: "num", text: thousands(period) }), el("td", { class: "num", text: pick("along").share.toFixed(2) }), el("td", { class: "num", text: pick("across").share.toFixed(2) })));
  }
  $("groups-2d").replaceChildren(...rows);
  // Top view: the outline of the sensor at the first frame and twenty frames later, over the picture's outline.
  const W = 420, H = 270, pictureW = width * out.dx_nm, pictureH = height * out.dx_nm;
  const f = out.footprint, xs = [f[0], f[2], f[4], f[6]], ys = [f[1], f[3], f[5], f[7]];
  const minX = Math.min(0, ...xs), maxX = Math.max(pictureW, ...xs), minY = Math.min(0, ...ys), maxY = Math.max(pictureH, ...ys);
  const scale = Math.min((W - 30) / (maxX - minX), (H - 80) / (maxY - minY));
  const PX = (x) => 15 + (x - minX) * scale, PY = (y) => 28 + (y - minY) * scale;
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "The sensor outline from above, over the picture" });
  root.append(svg("rect", { x: PX(0), y: PY(0), width: pictureW * scale, height: pictureH * scale, style: "fill:var(--pill);stroke:var(--fg2)" }));
  const outline = (shift, style) => svg("polygon", { points: [0, 1, 2, 3].map((k) => `${PX(xs[k] + shift)},${PY(ys[k])}`).join(" "), style });
  root.append(outline(20 * out.step_nm, "fill:none;stroke:var(--accent);stroke-dasharray:4 3"));
  root.append(outline(0, "fill:var(--accent);fill-opacity:0.2;stroke:var(--accent);stroke-width:1.5"));
  root.append(svg("text", { x: 15, y: 16 }, "Grey: the picture. Blue: the sensor at the first frame."));
  root.append(svg("text", { x: 15, y: H - 22 }, "Dashed: the sensor 20 frames later. Drawn to scale."));
  root.append(svg("text", { x: 15, y: H - 6 }, `The scan runs left to right, ${thousands(out.step_nm)} nm per frame.`));
  $("footprint").replaceChildren(root);
}

// ---------------------------------------------------------------------- start

function selectTab(which) {
  $("view-1d").hidden = which !== "1d"; $("view-2d").hidden = which !== "2d";
  $("tab-1d").setAttribute("aria-selected", String(which === "1d")); $("tab-2d").setAttribute("aria-selected", String(which === "2d"));
  saveToAddress();
  if (which === "1d") { redraw1(); run1(); } else run2();
}

async function start() {
  info = await (await fetch("/api/describe")).json();
  const saved = loadFromAddress();
  state = (saved && saved.s) || clone(info.default);
  state2 = (saved && saved.s2) || clone(info.default_2d);

  const groups = { optics: $("group-optics"), scan: $("group-scan"), noise: $("group-noise") };
  for (const def of info.controls) groups[def.key.split(".")[0]].append(buildControl(def, () => state, changed1));
  buildMethods();
  for (const def of info.controls_2d) $("group-2d").append(buildControl(def, () => state2, changed2));

  const preset = $("preset");
  preset.append(el("option", { value: "", text: "Defaults (least squares)" }));
  for (const p of info.presets) preset.append(el("option", { value: p.name, text: p.name }));
  preset.addEventListener("change", () => {
    const chosen = info.presets.find((p) => p.name === preset.value);
    const keep = { scene: state.scene, seed: state.seed };
    state = { ...clone(chosen ? chosen.request : info.default), ...keep };
    $("preset-help").textContent = chosen ? chosen.description : "";
    changed1();
  });
  const scene = $("scene");
  for (const s of info.scenes) scene.append(el("option", { value: s.name, text: s.label }));
  scene.addEventListener("change", () => { state.scene = scene.value; changed1(); });
  syncers.push(() => { scene.value = state.scene; $("seed").value = state.seed; });
  $("seed").addEventListener("change", () => { state.seed = Math.max(0, Math.round(Number($("seed").value) || 0)); changed1(); });
  $("reseed").addEventListener("click", () => { state.seed += 1; changed1(); });
  $("reset").addEventListener("click", () => { state = clone(info.default); preset.value = ""; $("preset-help").textContent = ""; changed1(); });
  for (const radio of document.querySelectorAll('input[name="positions"]')) {
    radio.addEventListener("change", () => { state.positions = radio.value; changed1(); });
    syncers.push(() => { radio.checked = state.positions === radio.value; });
  }
  $("show-seen").addEventListener("change", drawSurface);
  $("file-method").addEventListener("change", showFile);
  $("copy").addEventListener("click", async () => {
    $("file").select();
    try { await navigator.clipboard.writeText($("file").value); $("copy").textContent = "Copied"; } catch (e) { document.execCommand("copy"); }
    setTimeout(() => { $("copy").textContent = "Copy"; }, 1500);
  });

  const method2 = $("method-2d");
  for (const m of info.methods_2d) method2.append(el("option", { value: m.name, text: m.label }));
  method2.addEventListener("change", () => { state2.method = method2.value; changed2(); });
  $("seed-2d").addEventListener("change", () => { state2.seed = Math.max(0, Math.round(Number($("seed-2d").value) || 0)); changed2(); });
  $("reset-2d").addEventListener("click", () => { state2 = clone(info.default_2d); changed2(); });
  syncers.push(() => {
    method2.value = state2.method; $("seed-2d").value = state2.seed;
    document.querySelector('[data-key="smoothness"]').classList.toggle("off", state2.method !== "least_squares");
  });

  run1 = makeRunner("/api/run", () => state, show1, $("status"));
  run2 = makeRunner("/api/run2d", () => state2, show2, $("status-2d"));
  $("tab-1d").addEventListener("click", () => selectTab("1d"));
  $("tab-2d").addEventListener("click", () => selectTab("2d"));
  surfaceInteraction();
  let resizeTimer = null;
  window.addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(redraw1, 100); });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { redraw1(); drawSetup(); });

  syncAll();
  changed1();
  if (saved && saved.tab === "2d") selectTab("2d");
}

start();
