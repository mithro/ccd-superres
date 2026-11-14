/* Trade-off explorer page. All numbers come from model.js. */
(function () {
  "use strict";
  const M = window.CCDModel;
  const $ = (sel, el) => (el || document).querySelector(sel);
  const h = (tag, attrs, ...kids) => {
    const el = document.createElement(tag);
    for (const k in attrs || {}) {
      if (k === "class") el.className = attrs[k];
      else if (k === "text") el.textContent = attrs[k];
      else el.setAttribute(k, attrs[k]);
    }
    for (const kid of kids) if (kid != null) el.append(kid);
    return el;
  };
  const SVG = "http://www.w3.org/2000/svg";
  const s = (tag, attrs) => {
    const el = document.createElementNS(SVG, tag);
    for (const k in attrs || {}) el.setAttribute(k, attrs[k]);
    return el;
  };

  // ---------- formatting ----------
  const sig = (x, n) => {
    if (!isFinite(x)) return "∞";
    if (x === 0) return "0";
    const v = Number(x.toPrecision(n || 3));
    return Math.abs(v) >= 1e6 || Math.abs(v) < 1e-3 ? v.toExponential(1) : String(v);
  };
  const fmtLen = (nm) => {
    if (!isFinite(nm)) return "none";
    if (nm < 1e3) return sig(nm) + " nm";
    if (nm < 1e6) return sig(nm / 1e3) + " µm";
    return sig(nm / 1e6) + " mm";
  };
  const fmtTime = (sec) => {
    if (!isFinite(sec)) return "∞";
    if (sec < 1e-3) return sig(sec * 1e6) + " µs";
    if (sec < 1) return sig(sec * 1e3) + " ms";
    if (sec < 120) return sig(sec) + " s";
    if (sec < 7200) return sig(sec / 60) + " min";
    if (sec < 172800) return sig(sec / 3600) + " h";
    return sig(sec / 86400) + " days";
  };
  const fmtCount = (n) => {
    if (!isFinite(n)) return "∞";
    if (n >= 1e9) return sig(n / 1e9) + " billion";
    if (n >= 1e6) return sig(n / 1e6) + " million";
    if (n >= 1e4) return Math.round(n).toLocaleString("en-US");
    return sig(n);
  };

  // ---------- controls ----------
  const log = (min, max) => ({
    toV: (t) => min * Math.pow(max / min, t),
    toT: (v) => Math.log(v / min) / Math.log(max / min),
  });
  const lin = (min, max) => ({ toV: (t) => min + (max - min) * t, toT: (v) => (v - min) / (max - min) });

  const CONTROLS = [
    { group: "Scan" },
    { id: "fraction", label: "Speed", scale: log(1e-4, 2), def: 0.2,
      fmt: (v, r) => sig(v * 100) + "% of sensor per second · " + (r ? sig(r.speedUmPerS) + " µm/s" : "") },
    { id: "fps", label: "Frame rate", scale: log(1, 200), def: 10, fmt: (v) => sig(v) + " frames/s" },
    { id: "exposure", label: "Exposure or light pulse", scale: log(1e-5, 1), def: 1,
      fmt: (v, r) => (v > 0.999 ? "continuous · " : sig(v * 100) + "% of frame · ") + (r ? fmtTime(r.exposureS) : "") },
    { id: "tilt", label: "Sensor tilt", scale: lin(0, 0.2), def: 0,
      fmt: (v) => "tan θ = " + v.toFixed(4) + " · " + (Math.atan(v) * 180 / Math.PI).toFixed(2) + "°" },
    { id: "jitter", label: "Random position error per frame", scale: lin(0, 2), def: 0,
      fmt: (v) => v.toFixed(2) + " px rms" },
    { id: "passes", label: "Passes over the surface", scale: log(1, 1000), def: 1, round: true,
      fmt: (v) => String(v) },
    { group: "Instrument" },
    { id: "gap", label: "Gap, sensor to surface", scale: log(10, 1e6), def: 3000, fmt: (v) => fmtLen(v) },
    { id: "edge", label: "Pixel edge softness", scale: lin(0, 1000), def: 0, fmt: (v) => fmtLen(v) || "0" },
    { id: "mask", label: "Light-sensitive width of a pixel", scale: log(0.02, 1), def: 1,
      fmt: (v, r) => (v > 0.999 ? "whole pixel" : "masked to " + (r ? fmtLen(v * r.pitchNm) : "")) },
    { id: "wavelength", label: "Wavelength (collimated light only)", scale: log(150, 1000), def: 405, fmt: (v) => fmtLen(v) },
    { group: "Signal" },
    { id: "snr", label: "Signal-to-noise of one sample", scale: log(5, 500), def: 50, fmt: (v) => sig(v) },
    { id: "contrast", label: "Feature contrast", scale: log(0.01, 1), def: 1, fmt: (v) => sig(v * 100) + "%" },
  ];

  const PRESETS = [
    { name: "20% per second at 10 frames/s", set: { fraction: 0.2, fps: 10, exposure: 1, tilt: 0, jitter: 0, passes: 1 } },
    { name: "Same, 0.3 ms light pulse and tilt", set: { fraction: 0.2, fps: 10, exposure: 0.003, tilt: 0.0625, jitter: 0, passes: 1 } },
    { name: "Same, pulse and natural jitter only", set: { fraction: 0.2, fps: 10, exposure: 0.003, tilt: 0, jitter: 0.5, passes: 1 } },
    { name: "Slow scan, quarter pixel per frame", set: { fraction: 0.25 * 30 / 3280, fps: 30, exposure: 1, tilt: 0.0625, jitter: 0, passes: 1 } },
    { name: "100 nm features on silicon", set: { fraction: 0.05 * 30 / 3280, fps: 30, exposure: 1, tilt: 0.0625, jitter: 0, passes: 1,
      gap: 100, edge: 0, mask: 100 / 1120, wavelength: 405, gapModel: "collimated", sensor: "imx219" } },
  ];

  const state = { sensor: "imx219", sweep: "gap", gapModel: "diffuse" };
  const TARGET_NM = 200;   // 100 nm lines and spaces
  CONTROLS.forEach((c) => { if (c.id) state[c.id] = c.def; });

  function params(over) {
    const st = Object.assign({}, state, over || {});
    return {
      sensor: M.SENSORS[st.sensor],
      fractionPerS: st.fraction, fps: st.fps, exposureFraction: st.exposure, tiltTan: st.tilt,
      jitterPx: st.jitter, passes: st.passes, gapNm: st.gap, edgeSigmaNm: st.edge,
      snrSingle: st.snr, contrast: st.contrast,
      gapModel: st.gapModel, wavelengthNm: st.wavelength,
      apertureNm: st.mask * M.SENSORS[st.sensor].pitchUm * 1e3,
    };
  }

  // ---------- charts ----------
  const PAD = { l: 58, r: 14, t: 12, b: 40 };

  function logTicks(min, max) {
    const out = [];
    for (let e = Math.ceil(Math.log10(min) - 1e-9); e <= Math.floor(Math.log10(max) + 1e-9); e++) out.push(Math.pow(10, e));
    return out;
  }

  /* Log-log line chart with a crosshair and tooltip. */
  function lineChart(host, cfg) {
    // Draw at the container's own pixel size so text stays the same size everywhere.
    const W = Math.max(280, Math.round(host.clientWidth || 560));
    const H = Math.round(Math.max(230, Math.min(340, W * 0.62)));
    host.textContent = "";
    const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": cfg.aria });
    const lx = (v) => PAD.l + (Math.log10(v / cfg.x[0]) / Math.log10(cfg.x[1] / cfg.x[0])) * (W - PAD.l - PAD.r);
    const ly = (v) => H - PAD.b - (Math.log10(v / cfg.y[0]) / Math.log10(cfg.y[1] / cfg.y[0])) * (H - PAD.t - PAD.b);
    const xt = logTicks(cfg.x[0], cfg.x[1]), yt = logTicks(cfg.y[0], cfg.y[1]);
    const xStep = Math.ceil(xt.length / Math.max(3, Math.floor((W - PAD.l - PAD.r) / 70))), yStep = Math.ceil(yt.length / 7);
    xt.forEach((v, i) => {
      svg.append(s("line", { class: "tick", x1: lx(v), x2: lx(v), y1: PAD.t, y2: H - PAD.b }));
      if (i % xStep === 0) {
        const t = s("text", { x: lx(v), y: H - PAD.b + 14, "text-anchor": "middle" });
        t.textContent = cfg.xFmt(v);
        svg.append(t);
      }
    });
    yt.forEach((v, i) => {
      svg.append(s("line", { class: "tick", x1: PAD.l, x2: W - PAD.r, y1: ly(v), y2: ly(v) }));
      if (i % yStep === 0) {
        const t = s("text", { x: PAD.l - 6, y: ly(v) + 4, "text-anchor": "end" });
        t.textContent = cfg.yFmt(v);
        svg.append(t);
      }
    });
    svg.append(s("line", { class: "axis", x1: PAD.l, x2: W - PAD.r, y1: H - PAD.b, y2: H - PAD.b }));
    const xl = s("text", { x: (PAD.l + W - PAD.r) / 2, y: H - 6, "text-anchor": "middle" });
    xl.textContent = cfg.xLabel;
    svg.append(xl);
    const yl = s("text", { x: 12, y: (PAD.t + H - PAD.b) / 2, "text-anchor": "middle",
      transform: `rotate(-90 12 ${(PAD.t + H - PAD.b) / 2})` });
    yl.textContent = cfg.yLabel;
    svg.append(yl);

    const clipId = "clip-" + cfg.id;
    const defs = s("defs");
    const clip = s("clipPath", { id: clipId });
    clip.append(s("rect", { x: PAD.l, y: PAD.t, width: W - PAD.l - PAD.r, height: H - PAD.t - PAD.b }));
    defs.append(clip);
    svg.append(defs);
    const plot = s("g", { "clip-path": `url(#${clipId})` });
    svg.append(plot);
    const floor = cfg.y[0] / 10;
    for (const ser of cfg.series) {
      let d = "";
      let pen = false;
      for (const [x, y] of ser.points) {
        if (!isFinite(y)) { pen = false; continue; }
        d += (pen ? "L" : "M") + lx(x).toFixed(1) + " " + ly(Math.max(y, floor)).toFixed(1);
        pen = true;
      }
      plot.append(s("path", { d: d, fill: "none", stroke: `var(${ser.color})`, "stroke-width": ser.width || 2,
        "stroke-dasharray": ser.dash || "", "stroke-linejoin": "round" }));
    }
    for (const bd of cfg.bands || []) {
      svg.append(s("line", { x1: lx(bd.x), x2: lx(bd.x), y1: PAD.t, y2: H - PAD.b, stroke: "var(--s-pixel)", "stroke-width": 1.5 }));
      const t = s("text", { x: lx(bd.x) + 5, y: PAD.t + 11 });
      t.textContent = bd.label;
      t.style.fill = "var(--fg)";
      svg.append(t);
    }
    for (const bd of cfg.hbands || []) {
      if (bd.y < cfg.y[0] || bd.y > cfg.y[1]) continue;
      svg.append(s("line", { x1: PAD.l, x2: W - PAD.r, y1: ly(bd.y), y2: ly(bd.y), stroke: "var(--s-pixel)", "stroke-width": 1.5 }));
      const t = s("text", { x: W - PAD.r - 4, y: ly(bd.y) - 5, "text-anchor": "end" });
      t.textContent = bd.label;
      t.style.fill = "var(--fg)";
      svg.append(t);
    }
    for (const mk of cfg.markers || []) {
      if (!isFinite(mk.x) || mk.x < cfg.x[0] || mk.x > cfg.x[1]) continue;
      svg.append(s("line", { x1: lx(mk.x), x2: lx(mk.x), y1: PAD.t, y2: H - PAD.b, stroke: "var(--fg)",
        "stroke-width": 1, "stroke-dasharray": "2 3" }));
      if (mk.y != null && isFinite(mk.y) && mk.y >= cfg.y[0] && mk.y <= cfg.y[1]) {
        svg.append(s("circle", { cx: lx(mk.x), cy: ly(mk.y), r: 5, fill: "var(--fg)", stroke: "var(--panel)", "stroke-width": 2 }));
      }
      const flip = lx(mk.x) > W - 150;
      const t = s("text", { x: lx(mk.x) + (flip ? -6 : 6), y: mk.low ? H - PAD.b - 8 : PAD.t + 11, "text-anchor": flip ? "end" : "start" });
      t.textContent = mk.label;
      t.style.fill = "var(--fg)";
      svg.append(t);
    }
    const cross = s("line", { class: "cross", y1: PAD.t, y2: H - PAD.b, visibility: "hidden" });
    svg.append(cross);
    host.append(svg);
    const tip = h("div", { class: "tip", hidden: "" });
    host.append(tip);

    const move = (ev) => {
      const r = svg.getBoundingClientRect();
      const px = ((ev.clientX - r.left) / r.width) * W;
      if (px < PAD.l || px > W - PAD.r) { leave(); return; }
      const xv = cfg.x[0] * Math.pow(cfg.x[1] / cfg.x[0], (px - PAD.l) / (W - PAD.l - PAD.r));
      cross.setAttribute("x1", px);
      cross.setAttribute("x2", px);
      cross.setAttribute("visibility", "visible");
      tip.textContent = "";
      tip.append(h("b", { text: cfg.xTip(xv) }));
      for (const ser of cfg.series) {
        let best = ser.points[0];
        for (const p of ser.points) if (Math.abs(Math.log(p[0] / xv)) < Math.abs(Math.log(best[0] / xv))) best = p;
        tip.append(h("div", { text: ser.name + ": " + cfg.yTip(best[1]) }));
      }
      tip.hidden = false;
      const left = ((px / W) * r.width);
      tip.style.left = Math.max(0, Math.min(r.width - tip.offsetWidth, left + (left > r.width / 2 ? -tip.offsetWidth - 10 : 10))) + "px";
      tip.style.top = "8px";
    };
    const leave = () => { cross.setAttribute("visibility", "hidden"); tip.hidden = true; };
    svg.addEventListener("pointermove", move);
    svg.addEventListener("pointerleave", leave);
  }

  function coverageChart(host, r) {
    host.textContent = "";
    const S = 300, P = { l: 34, r: 10, t: 10, b: 34 };
    const svg = s("svg", { viewBox: `0 0 ${S} ${S}`, role: "img",
      "aria-label": "Positions inside one pixel at which a surface point is sampled" });
    const side = S - P.l - P.r;
    const X = (v) => P.l + v * side, Y = (v) => S - P.b - v * (S - P.t - P.b);
    svg.append(s("rect", { x: P.l, y: P.t, width: side, height: S - P.t - P.b, fill: "none", stroke: "var(--fg2)" }));
    [0, 0.5, 1].forEach((v) => {
      const a = s("text", { x: X(v), y: S - P.b + 14, "text-anchor": "middle" });
      a.textContent = String(v);
      const b = s("text", { x: P.l - 6, y: Y(v) + 4, "text-anchor": "end" });
      b.textContent = String(v);
      svg.append(a, b);
    });
    const xl = s("text", { x: P.l + side / 2, y: S - 4, "text-anchor": "middle" });
    xl.textContent = "along scan (pixels)";
    const yl = s("text", { x: 10, y: P.t + side / 2, "text-anchor": "middle", transform: `rotate(-90 10 ${P.t + side / 2})` });
    yl.textContent = "across scan (pixels)";
    svg.append(xl, yl);
    const pts = r.phases;
    const rad = pts.length > 300 ? 1.6 : pts.length > 80 ? 2.4 : 4;
    for (const p of pts) {
      const c = s("circle", { cx: X(p[0]).toFixed(1), cy: Y(p[1]).toFixed(1), r: rad, fill: "var(--s-gap)",
        stroke: "var(--panel)", "stroke-width": rad > 2 ? 1 : 0 });
      svg.append(c);
    }
    host.append(svg);
  }

  // ---------- sweep definitions ----------
  const SWEEPS = {
    gap: { label: "Gap", key: "gap", range: [10, 1e6], fmt: fmtLen, axis: "gap between sensor and surface" },
    fraction: { label: "Speed", key: "fraction", range: [1e-4, 2], fmt: (v) => sig(v * 100, 2) + "%/s", axis: "speed (sensor lengths per second)" },
    fps: { label: "Frame rate", key: "fps", range: [1, 200], fmt: (v) => sig(v, 2), axis: "frame rate (frames per second)" },
    wavelength: { label: "Wavelength", key: "wavelength", range: [150, 1000], fmt: fmtLen, axis: "wavelength (collimated light only)" },
    mask: { label: "Sensitive width", key: "mask", range: [0.02, 1], fmt: (v) => sig(v * 100, 2) + "%", axis: "light-sensitive width (share of the pixel pitch)" },
    edge: { label: "Edge softness", key: "edge", range: [5, 1000], fmt: fmtLen, axis: "pixel edge softness" },
    exposure: { label: "Exposure", key: "exposure", range: [1e-5, 1], fmt: (v) => sig(v * 100, 2) + "%", axis: "exposure (share of the frame period)" },
    snr: { label: "Signal-to-noise", key: "snr", range: [5, 500], fmt: (v) => sig(v, 2), axis: "signal-to-noise of one sample" },
    passes: { label: "Passes", key: "passes", range: [1, 1000], fmt: (v) => sig(v, 2), axis: "passes over the surface" },
  };

  // ---------- page ----------
  const refs = {};

  function build() {
    const root = $("#app");
    root.textContent = "";
    const wrap = h("div", { class: "wrap" });
    wrap.append(h("header", null,
      h("h1", { text: "Scan trade-off explorer" }),
      h("p", { text: "Change the scan, the instrument and the signal, and see at once how many samples each point on the surface gets, how they cover the sub-pixel positions, and the smallest feature the analytic model says can be recovered." })));

    const presets = h("div", { class: "presets", role: "group", "aria-label": "Presets" });
    PRESETS.forEach((p) => {
      const b = h("button", { class: "preset", type: "button", text: p.name });
      b.addEventListener("click", () => { Object.assign(state, p.set); syncControls(); update(); });
      presets.append(b);
    });
    wrap.append(presets);

    const layout = h("div", { class: "layout" });
    const controls = h("section", { class: "controls", "aria-label": "Settings" });
    const sensorSel = h("select", { id: "ctl-sensor" });
    for (const k in M.SENSORS) sensorSel.append(h("option", { value: k, text: M.SENSORS[k].name }));
    sensorSel.addEventListener("change", () => { state.sensor = sensorSel.value; update(); });
    refs.sensor = sensorSel;
    refs.sensorHint = h("span", { class: "hint" });
    controls.append(h("div", { class: "group" }, h("h2", { text: "Sensor" }),
      h("div", { class: "ctl" }, h("label", { for: "ctl-sensor", text: "Model" }), sensorSel, refs.sensorHint)));

    const modelSel = h("select", { id: "ctl-gapmodel" });
    modelSel.append(h("option", { value: "diffuse", text: "Matt surface, light from all directions" }),
      h("option", { value: "collimated", text: "Mirror-like surface, collimated light" }));
    modelSel.addEventListener("change", () => { state.gapModel = modelSel.value; update(); });
    refs.gapModel = modelSel;
    controls.append(h("div", { class: "group" }, h("h2", { text: "Surface and light" }),
      h("div", { class: "ctl" }, h("label", { for: "ctl-gapmodel", text: "How light crosses the gap" }), modelSel,
        h("span", { class: "hint", text: "A polished silicon chip is mirror-like." }))));

    let group = null;
    refs.ctl = {};
    CONTROLS.forEach((c) => {
      if (c.group) {
        group = h("div", { class: "group" }, h("h2", { text: c.group }));
        controls.append(group);
        return;
      }
      const input = h("input", { type: "range", id: "ctl-" + c.id, min: 0, max: 1000, step: 1 });
      const val = h("span", { class: "val" });
      input.addEventListener("input", () => {
        let v = c.scale.toV(input.value / 1000);
        if (c.round) v = Math.max(1, Math.round(v));
        state[c.id] = v;
        update();
      });
      refs.ctl[c.id] = { input, val, def: c };
      group.append(h("div", { class: "ctl" },
        h("label", { for: "ctl-" + c.id }, h("span", { text: c.label })), val, input));
    });
    layout.append(controls);

    const results = h("section", { class: "results", "aria-live": "off" });
    refs.tiles = h("div", { class: "tiles" });
    refs.notes = h("ul", { class: "notes" });
    results.append(refs.tiles, refs.notes);

    const charts = h("div", { class: "charts" });
    refs.cov = h("div", { class: "chart square" });
    refs.covCap = h("p", { class: "cap" });
    charts.append(h("div", { class: "card" }, h("h2", { text: "Where the samples of one point fall inside a pixel" }), refs.cov, refs.covCap));

    refs.tf = h("div", { class: "chart" });
    refs.tfTable = h("div");
    const legend = h("div", { class: "legend" });
    [["Gap", "--s-gap"], ["Pixel area", "--s-pixel"], ["Motion blur", "--s-motion"], ["All three", "--s-total"]].forEach(([n, c]) => {
      const i = h("i"); i.style.borderColor = `var(${c})`;
      legend.append(h("span", null, i, n));
    });
    const di = h("i", { class: "dash" }); di.style.borderColor = "var(--fg2)";
    legend.append(h("span", null, di, "Needed to beat the noise"));
    charts.append(h("div", { class: "card" }, h("h2", { text: "Contrast passed to the detector, by feature size" }), legend, refs.tf,
      h("p", { class: "cap", text: "A feature is recoverable where the “all three” line is above the dashed line. Box-shaped blurs are drawn as their envelope." }), refs.tfTable));

    refs.sweep = h("div", { class: "chart" });
    const sweepSel = h("select", { id: "ctl-sweep", "aria-label": "Quantity to sweep" });
    for (const k in SWEEPS) sweepSel.append(h("option", { value: k, text: SWEEPS[k].label }));
    sweepSel.addEventListener("change", () => { state.sweep = sweepSel.value; update(); });
    refs.sweepSel = sweepSel;
    charts.append(h("div", { class: "card wide" },
      h("div", { class: "head" }, h("h2", { text: "Smallest recoverable feature as one setting changes" }),
        h("label", { for: "ctl-sweep" }, "Sweep ", sweepSel)),
      refs.sweep,
      h("p", { class: "cap", text: "Everything else stays at its current value. The marker is the current setting. Spikes against speed or frame rate are real: they are settings where the shift per frame repeats and samples pile up on a few positions." })));
    results.append(charts);
    layout.append(results);
    wrap.append(layout);
    wrap.append(h("footer", null, h("p", { text: "These are instant analytic estimates, not simulation results. They assume exactly known sample positions, and judge a feature recoverable when its attenuated signal exceeds the averaged noise. Sub-pixel coverage is computed from at most 600 samples of a point." })));
    root.append(wrap);
    syncControls();
  }

  function syncControls() {
    refs.sensor.value = state.sensor;
    refs.gapModel.value = state.gapModel;
    refs.sweepSel.value = state.sweep;
    for (const id in refs.ctl) {
      const c = refs.ctl[id];
      c.input.value = Math.round(Math.max(0, Math.min(1, c.def.scale.toT(state[id]))) * 1000);
    }
  }

  function tile(k, v, sub, hero) {
    return h("div", { class: "tile" + (hero ? " hero" : "") }, h("div", { class: "k", text: k }),
      h("div", { class: "v", text: v }), sub ? h("div", { class: "s" }, sub) : null);
  }

  function update() {
    const r = M.explore(params());
    const sensor = M.SENSORS[state.sensor];
    refs.sensorHint.textContent = `${sensor.nAlong} × ${sensor.nAcross} pixels, ${sensor.pitchUm} µm pitch, ` +
      `${sig(sensor.nAlong * sensor.pitchUm / 1e3)} × ${sig(sensor.nAcross * sensor.pitchUm / 1e3)} mm`;
    for (const id in refs.ctl) refs.ctl[id].val.textContent = refs.ctl[id].def.fmt(state[id], r);

    const cov = r.coverage;
    const capped = r.samplesPerPoint > r.samplesComputed + 1;
    refs.tiles.textContent = "";
    const pill = h("span", null, "limited by ", h("span", { class: "pill", text: r.limitedBy }),
      ` · ${sig(r.recoverableNm / r.pitchNm)} × pixel pitch`);
    refs.tiles.append(
      tile("Smallest recoverable feature period", fmtLen(r.recoverableNm), pill, true),
      tile("Target: 100 nm lines and spaces", r.recoverableNm <= TARGET_NM ? "resolved" : "not resolved",
        r.recoverableNm <= TARGET_NM ? "200 nm period is within reach of this setting"
          : `needs ${sig(r.recoverableNm / TARGET_NM, 2)} × finer than this setting gives`),
      tile("Samples per surface point", fmtCount(r.samplesPerPoint * state.passes),
        `a point is under the sensor for ${fmtTime(r.timeUnderSensorS)}` + (state.passes > 1 ? ` per pass` : "")),
      tile("Shift per frame", sig(r.shiftPx) + " px", `${sig(r.shiftXPx)} along, ${sig(r.shiftYPx)} across`),
      tile("Motion blur", sig(r.blurPx) + " px", `quarter-pixel blur needs ${fmtTime(r.exposureForQuarterPxS)}`),
      tile("Distinct sub-pixel positions", (capped ? "≥ " : "") + fmtCount(cov.distinct),
        `largest hole ${capped ? "≤ " : ""}${sig(cov.holePx, 2)} px (perfect grid ${sig(cov.idealHolePx, 2)})`),
      tile("Area covered", sig(r.areaUm2PerS / 1e6) + " mm²/s", `1 cm² in ${fmtTime(100 / (r.areaUm2PerS / 1e6) * state.passes)}`),
      tile("Data rate", fmtCount(r.samplesPerS) + "/s", "pixel samples recorded"));

    refs.notes.textContent = "";
    const notes = [];
    if (r.blurPx > 1) notes.push(`Motion blur is ${sig(r.blurPx)} pixels. For sub-pixel work the exposure or light pulse must be about ${fmtTime(r.exposureForQuarterPxS)} or shorter, or the scan slower.`);
    if (state.tilt === 0 && state.jitter === 0) notes.push("No tilt and no position error: every sample of a point lands at the same place across the scan, so nothing is gained in that direction.");
    if (!capped && cov.distinct < cov.nSamples) notes.push(`Only ${cov.distinct} distinct sub-pixel positions among ${cov.nSamples} samples: the shift per frame repeats exactly. A slightly different speed, or natural position error, breaks the repeat.`);
    if (state.gap > r.pitchNm) notes.push("The gap is larger than a pixel, so the gap sets the resolution and sub-pixel sampling cannot improve on it.");
    notes.forEach((n) => refs.notes.append(h("li", { text: n })));

    coverageChart(refs.cov, r);
    refs.covCap.textContent = `${r.samplesComputed}${capped ? " of " + fmtCount(r.samplesPerPoint) : ""} samples shown. Widest gap ${sig(cov.gapAlongPx, 2)} px along the scan and ${sig(cov.gapAcrossPx, 2)} px across it.`;

    const xr = [10, 1e7], periods = [];
    for (let i = 0; i <= 160; i++) periods.push(xr[0] * Math.pow(xr[1] / xr[0], i / 160));
    const pn = r.pitchNm;
    lineChart(refs.tf, {
      id: "tf", aria: "Contrast passed by each stage against feature period",
      x: xr, y: [1e-6, 2], xLabel: "feature period", yLabel: "contrast (1 = full)",
      xFmt: fmtLen, yFmt: (v) => (v >= 0.01 ? String(v) : "1e" + Math.round(Math.log10(v))),
      xTip: (v) => "period " + fmtLen(v), yTip: (v) => sig(v, 2),
      series: [
        { name: "Gap", color: "--s-gap", points: periods.map((p) => [p, M.gapTransfer(p, state.gap, r.optics.gapModel, r.optics.wavelengthNm)]) },
        { name: "Pixel area", color: "--s-pixel", points: periods.map((p) => [p, M.pixelTransfer(p, r.optics.apertureNm, state.edge)]) },
        { name: "Motion blur", color: "--s-motion", points: periods.map((p) => [p, M.boxEnvelope(p, r.blurPx * pn)]) },
        { name: "All three", color: "--s-total", width: 2.5, points: periods.map((p) => [p, M.combinedTransfer(p, state.gap, pn, r.blurPx, state.edge, r.optics)]) },
        { name: "Needed", color: "--fg2", dash: "5 4", width: 1.5, points: periods.map((p) => [p, M.requiredTransfer(p, r.samplesPerPixelArea, pn, r.snrEffective, r.contrast)]) },
      ],
      markers: [{ x: r.recoverableNm, low: true, label: "recoverable from " + fmtLen(r.recoverableNm) }],
      bands: [{ x: TARGET_NM, label: "target 200 nm" }],
    });
    refs.tfTable.textContent = "";
    const tb = h("table", { class: "mini" });
    tb.append(h("tr", null, h("th", { text: "At " + fmtLen(r.recoverableNm) }), h("th", { text: "Contrast passed" })));
    [["Gap", r.transferGap], ["Pixel area", r.transferPixel], ["Motion blur", r.transferMotion]].forEach(([n, v]) =>
      tb.append(h("tr", null, h("td", { text: n }), h("td", { class: "num", text: sig(v, 2) }))));
    refs.tfTable.append(tb);

    const sw = SWEEPS[state.sweep];
    const pts = [];
    const fast = { maxSamples: 200, grid: 24 };
    for (let i = 0; i <= 70; i++) {
      let v = sw.range[0] * Math.pow(sw.range[1] / sw.range[0], i / 70);
      if (sw.key === "passes") v = Math.max(1, Math.round(v));
      const o = {}; o[sw.key] = v;
      pts.push([v, M.explore(params(o), fast).recoverableNm]);
    }
    const here = M.explore(params(), fast).recoverableNm;
    const ys = pts.map((p) => p[1]).filter(isFinite).concat(isFinite(here) ? [here] : []);
    const ymin = Math.pow(10, Math.floor(Math.log10(Math.min.apply(null, ys.concat([pn, TARGET_NM])) * 0.8)));
    const ymax = Math.pow(10, Math.ceil(Math.log10(Math.max.apply(null, ys.concat([pn])) * 1.2)));
    lineChart(refs.sweep, {
      id: "sweep", aria: "Smallest recoverable feature period against " + sw.label.toLowerCase(),
      x: sw.range, y: [ymin, ymax], xLabel: sw.axis, yLabel: "recoverable period",
      xFmt: sw.fmt, yFmt: fmtLen, xTip: (v) => sw.label + " " + sw.fmt(v), yTip: fmtLen,
      series: [
        { name: "Recoverable period", color: "--s-gap", points: pts },
        { name: "Pixel pitch", color: "--fg2", dash: "2 3", width: 1, points: [[sw.range[0], pn], [sw.range[1], pn]] },
      ],
      markers: [{ x: state[sw.key], y: here, label: "now: " + fmtLen(here) }],
      hbands: [{ y: TARGET_NM, label: "target: 200 nm period (100 nm features)" }],
    });
  }

  build();
  update();
  let lastWidth = window.innerWidth, timer = null;
  window.addEventListener("resize", () => {
    if (window.innerWidth === lastWidth) return;
    lastWidth = window.innerWidth;
    clearTimeout(timer);
    timer = setTimeout(update, 120);
  });
})();
