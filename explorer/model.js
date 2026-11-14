/* Analytic model behind the trade-off explorer.
 *
 * Mirrors ccdsr/sampling.py and ccdsr/resolution.py. It is kept free of any
 * page code so that tests/test_explorer_parity.py can run it under Node and
 * compare it with the Python package.
 *
 * Lengths: pixels unless a name ends in Um (micrometres) or Nm (nanometres).
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.CCDModel = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const SENSORS = {
    imx219: { name: "Camera Module 2 (IMX219)", nAlong: 3280, nAcross: 2464, pitchUm: 1.12 },
    imx708: { name: "Camera Module 3 (IMX708)", nAlong: 4608, nAcross: 2592, pitchUm: 1.4 },
    imx477: { name: "HQ Camera (IMX477)", nAlong: 4056, nAcross: 3040, pitchUm: 1.55 },
    imx296: { name: "Global Shutter Camera (IMX296)", nAlong: 1456, nAcross: 1088, pitchUm: 3.45 },
  };

  // Modified Bessel functions, polynomial approximations (Abramowitz and Stegun 9.8).
  function besselI1(x) {
    const ax = Math.abs(x);
    let ans;
    if (ax < 3.75) {
      const y = (x / 3.75) * (x / 3.75);
      ans = ax * (0.5 + y * (0.87890594 + y * (0.51498869 + y * (0.15084934 +
        y * (0.02658733 + y * (0.00301532 + y * 0.00032411))))));
    } else {
      const y = 3.75 / ax;
      ans = 0.02282967 + y * (-0.02895312 + y * (0.01787654 - y * 0.00420059));
      ans = 0.39894228 + y * (-0.03988024 + y * (-0.00362018 + y * (0.00163801 +
        y * (-0.01031555 + y * ans))));
      ans *= Math.exp(ax) / Math.sqrt(ax);
    }
    return x < 0 ? -ans : ans;
  }

  function besselK1(x) {
    if (x <= 2) {
      const y = (x * x) / 4;
      return Math.log(x / 2) * besselI1(x) + (1 / x) * (1 + y * (0.15443144 +
        y * (-0.67278579 + y * (-0.18156897 + y * (-0.01919402 +
        y * (-0.00110404 + y * -0.00004686))))));
    }
    const y = 2 / x;
    return (Math.exp(-x) / Math.sqrt(x)) * (1.25331414 + y * (0.23498619 +
      y * (-0.0365562 + y * (0.01504268 + y * (-0.00780353 +
      y * (0.00325614 + y * -0.00068245))))));
  }

  function sinc(x) {
    if (x === 0) return 1;
    const a = Math.PI * x;
    return Math.sin(a) / a;
  }

  function gapTransfer(periodNm, gapNm) {
    const u = (2 * Math.PI * gapNm) / periodNm;
    if (u < 1e-8) return 1;
    if (u > 700) return 0;
    return u * besselK1(u);
  }

  function boxEnvelope(periodNm, widthNm) {
    const x = widthNm / periodNm;
    if (x <= 0) return 1;
    return Math.min(Math.abs(sinc(Math.min(x, 0.5))), 1 / (Math.PI * Math.max(x, 1e-9)));
  }

  function softEdge(periodNm, sigmaNm) {
    const r = sigmaNm / periodNm;
    return Math.exp(-2 * Math.PI * Math.PI * r * r);
  }

  function pixelTransfer(periodNm, pitchNm, edgeSigmaNm) {
    return boxEnvelope(periodNm, pitchNm) * softEdge(periodNm, edgeSigmaNm);
  }

  function combinedTransfer(periodNm, gapNm, pitchNm, blurPx, edgeSigmaNm) {
    return gapTransfer(periodNm, gapNm) * pixelTransfer(periodNm, pitchNm, edgeSigmaNm) *
      boxEnvelope(periodNm, blurPx * pitchNm);
  }

  /* Contrast a feature of this period needs for its signal to equal the noise. */
  function requiredTransfer(periodNm, nPerPixelArea, pitchNm, snrSingle, contrast) {
    const nCell = nPerPixelArea * Math.pow(periodNm / (2 * pitchNm), 2);
    return 1 / (contrast * snrSingle * Math.sqrt(nCell));
  }

  function recoverablePeriod(nPerPixelArea, gapNm, pitchNm, snrSingle, contrast, blurPx,
    edgeSigmaNm) {
    const margin = (logP) => {
      const p = Math.exp(logP);
      return combinedTransfer(p, gapNm, pitchNm, blurPx, edgeSigmaNm) /
        requiredTransfer(p, nPerPixelArea, pitchNm, snrSingle, contrast) - 1;
    };
    let lo = Math.log(1e-2), hi = Math.log(1e12);
    if (margin(hi) < 0) return Infinity;
    for (let i = 0; i < 80; i++) {
      const mid = 0.5 * (lo + hi);
      if (margin(mid) >= 0) hi = mid; else lo = mid;
    }
    return Math.exp(hi);
  }

  // Small seeded generator so jittered patterns stay put while other controls move.
  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function gaussian(rand) {
    let u = 0;
    while (u === 0) u = rand();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rand());
  }

  function mod1(x) {
    const r = x - Math.floor(x);
    return r >= 1 ? 0 : r;
  }

  /* Sub-pixel positions at which one surface point is sampled, one per frame. */
  function samplePhases(sensor, scan, maxSamples) {
    const shift = scan.speedUmPerS / scan.fps / sensor.pitchUm;
    const cos = 1 / Math.hypot(1, scan.tiltTan);
    const sin = scan.tiltTan * cos;
    const nFull = shift > 0 ? Math.max(Math.floor(sensor.nAlong / (shift * cos) + 1e-9), 1) : 1;
    const n = Math.min(nFull, maxSamples || nFull);
    const rand = mulberry32(12345);
    const out = new Array(n);
    for (let k = 0; k < n; k++) {
      let x = k * shift * cos, y = k * shift * sin;
      if (scan.jitterPx > 0) {
        x += scan.jitterPx * gaussian(rand);
        y += scan.jitterPx * gaussian(rand);
      }
      out[k] = [mod1(Math.round(x * 1e9) / 1e9), mod1(Math.round(y * 1e9) / 1e9)];
    }
    return { phases: out, nFull: nFull };
  }

  function largestGap(values) {
    if (!values.length) return 1;
    const s = values.slice().sort((a, b) => a - b);
    let g = s[0] + 1 - s[s.length - 1];
    for (let i = 1; i < s.length; i++) g = Math.max(g, s[i] - s[i - 1]);
    return g;
  }

  /* Radius of the largest empty circle among points on the unit torus (grid probe). */
  function largestHole(phases, grid) {
    const g = grid || 40;
    // Bucket the points so each probe only looks at nearby ones.
    const nb = Math.max(1, Math.min(32, Math.floor(Math.sqrt(phases.length))));
    const buckets = Array.from({ length: nb * nb }, () => []);
    for (const p of phases) {
      const bx = Math.min(nb - 1, Math.floor(p[0] * nb));
      const by = Math.min(nb - 1, Math.floor(p[1] * nb));
      buckets[bx * nb + by].push(p);
    }
    let worst = 0;
    for (let i = 0; i < g; i++) {
      for (let j = 0; j < g; j++) {
        const qx = (i + 0.5) / g, qy = (j + 0.5) / g;
        const cx = Math.floor(qx * nb), cy = Math.floor(qy * nb);
        let best = Infinity;
        for (let ring = 0; ring <= Math.ceil(nb / 2); ring++) {
          // Nothing in a further ring can beat the current best.
          if (best < Infinity && (ring - 1) / nb > Math.sqrt(best)) break;
          for (let dx = -ring; dx <= ring; dx++) {
            for (let dy = -ring; dy <= ring; dy++) {
              if (Math.max(Math.abs(dx), Math.abs(dy)) !== ring) continue;
              const bx = ((cx + dx) % nb + nb) % nb, by = ((cy + dy) % nb + nb) % nb;
              for (const p of buckets[bx * nb + by]) {
                let ex = Math.abs(p[0] - qx), ey = Math.abs(p[1] - qy);
                if (ex > 0.5) ex = 1 - ex;
                if (ey > 0.5) ey = 1 - ey;
                const d2 = ex * ex + ey * ey;
                if (d2 < best) best = d2;
              }
            }
          }
        }
        if (best > worst) worst = best;
      }
    }
    return Math.sqrt(worst);
  }

  function coverage(phases, grid) {
    const seen = new Set();
    for (const p of phases) seen.add(Math.round(p[0] * 1e6) % 1e6 + "," + Math.round(p[1] * 1e6) % 1e6);
    const n = phases.length;
    const hole = largestHole(phases, grid);
    const ideal = n ? Math.sqrt(0.5 / n) : Infinity;
    return {
      nSamples: n,
      distinct: seen.size,
      gapAlongPx: largestGap(phases.map((p) => p[0])),
      gapAcrossPx: largestGap(phases.map((p) => p[1])),
      holePx: hole,
      idealHolePx: ideal,
      efficiency: hole > 0 ? ideal / hole : 1,
    };
  }

  /* Everything for one setting.
   *
   * params: sensor {nAlong, nAcross, pitchUm}; fractionPerS or speedUmPerS; fps;
   * exposureFraction (1 = continuous) or exposureS; tiltTan; jitterPx; gapNm;
   * snrSingle; contrast; edgeSigmaNm; passes.
   * opts: maxSamples and grid trade accuracy of the coverage figures for speed.
   */
  function explore(params, opts) {
    const o = opts || {};
    const sensor = params.sensor;
    const lengthUm = sensor.nAlong * sensor.pitchUm;
    const widthUm = sensor.nAcross * sensor.pitchUm;
    const speed = params.speedUmPerS != null ? params.speedUmPerS : params.fractionPerS * lengthUm;
    const frameS = 1 / params.fps;
    const exposureS = params.exposureS != null ? params.exposureS
      : (params.exposureFraction != null ? params.exposureFraction : 1) * frameS;
    const tiltTan = params.tiltTan || 0;
    const cos = 1 / Math.hypot(1, tiltTan);
    const sin = tiltTan * cos;
    const shift = speed / params.fps / sensor.pitchUm;
    const blurPx = (speed * exposureS) / sensor.pitchUm;
    const samplesPerPoint = shift > 0 ? sensor.nAlong / (shift * cos) : Infinity;
    const scan = { speedUmPerS: speed, fps: params.fps, tiltTan: tiltTan, jitterPx: params.jitterPx || 0 };
    const sp = samplePhases(sensor, scan, o.maxSamples || 600);
    const cov = coverage(sp.phases, o.grid || 40);
    const pitchNm = sensor.pitchUm * 1e3;
    const passes = params.passes || 1;
    const n = samplesPerPoint * passes;
    const snr = params.snrSingle != null ? params.snrSingle : 50;
    const contrast = params.contrast != null ? params.contrast : 1;
    const edge = params.edgeSigmaNm || 0;
    const noiseNm = recoverablePeriod(n, params.gapNm, pitchNm, snr, contrast, blurPx, edge);
    const samplingNm = 2 * Math.SQRT2 * cov.holePx * pitchNm;
    const period = Math.max(noiseNm, samplingNm);
    const tGap = isFinite(period) ? gapTransfer(period, params.gapNm) : 0;
    const tPix = isFinite(period) ? pixelTransfer(period, pitchNm, edge) : 0;
    const tMot = isFinite(period) ? boxEnvelope(period, blurPx * pitchNm) : 0;
    let limitedBy;
    if (samplingNm > noiseNm) limitedBy = "sampling pattern";
    else {
      limitedBy = "gap";
      let m = tGap;
      if (tPix < m) { m = tPix; limitedBy = "pixel area"; }
      if (tMot < m) { m = tMot; limitedBy = "motion blur"; }
    }
    return {
      speedUmPerS: speed,
      shiftPx: shift,
      shiftXPx: shift * cos,
      shiftYPx: shift * sin,
      samplesPerPoint: samplesPerPoint,
      samplesPerPixelArea: n,
      timeUnderSensorS: speed > 0 ? lengthUm / (speed * cos) : Infinity,
      exposureS: exposureS,
      blurPx: blurPx,
      exposureForQuarterPxS: shift > 0 ? (0.25 / shift) * frameS : frameS,
      samplesPerS: sensor.nAlong * sensor.nAcross * params.fps,
      areaUm2PerS: speed * cos * widthUm,
      phases: sp.phases,
      samplesComputed: sp.phases.length,
      coverage: cov,
      pitchNm: pitchNm,
      noiseLimitedNm: noiseNm,
      samplingLimitedNm: samplingNm,
      recoverableNm: period,
      limitedBy: limitedBy,
      transferGap: tGap,
      transferPixel: tPix,
      transferMotion: tMot,
      snrSingle: snr,
      contrast: contrast,
      edgeSigmaNm: edge,
      gapNm: params.gapNm,
    };
  }

  return {
    SENSORS, besselK1, gapTransfer, boxEnvelope, softEdge, pixelTransfer, combinedTransfer,
    requiredTransfer, recoverablePeriod, samplePhases, coverage, largestHole, explore,
  };
});
