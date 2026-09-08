// pointmap.js — proof-carrying point map for unlabeled latent space.
// Shared verbatim between the steady-orbit-sos Worker bundle and the /map/ browser page.
// Zero deps. Geometry matches sos-agent fit.ts (PCA2 → stereographic lift → S²).
// Spec: yubi-OS/yubiOS refs/point-to-point-latent-map-2026-09-06.md
var PM = (function () {
  function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function gauss(r) { let u = 0, v = 0; while (u === 0) u = r(); while (v === 0) v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
  function fnv1a64(bytes) { let h = 0xcbf29ce484222325n; for (const x of bytes) { h ^= BigInt(x); h = (h * 0x100000001b3n) & 0xffffffffffffffffn; } return h.toString(16).padStart(16, "0"); }
  const hashVec = (v) => fnv1a64(new Uint8Array(new Float32Array(v).buffer));
  const hashStr = (s) => fnv1a64(new TextEncoder().encode(s));
  // ---- linear algebra: Jacobi (small d) + power iteration (large D) ----
  function jacobiEig(A) { const n = A.length; const V = Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => i === j ? 1 : 0)); const M = A.map(r => r.slice());
    for (let sweep = 0; sweep < 80; sweep++) { let off = 0; for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) off += M[i][j] ** 2; if (off < 1e-14) break;
      for (let p = 0; p < n; p++) for (let q = p + 1; q < n; q++) { if (Math.abs(M[p][q]) < 1e-15) continue; const th = (M[q][q] - M[p][p]) / (2 * M[p][q]); const t = Math.sign(th || 1) / (Math.abs(th) + Math.sqrt(th * th + 1)); const c = 1 / Math.sqrt(t * t + 1), s = t * c;
        for (let k = 0; k < n; k++) { const a = M[k][p], b = M[k][q]; M[k][p] = c * a - s * b; M[k][q] = s * a + c * b; }
        for (let k = 0; k < n; k++) { const a = M[p][k], b = M[q][k]; M[p][k] = c * a - s * b; M[q][k] = s * a + c * b; }
        for (let k = 0; k < n; k++) { const a = V[k][p], b = V[k][q]; V[k][p] = c * a - s * b; V[k][q] = s * a + c * b; } } }
    const idx = M.map((_, i) => i).sort((a, b) => M[b][b] - M[a][a]); return { values: idx.map(i => M[i][i]), vectors: idx.map(i => V.map(r => r[i])) }; }
  function center(X) { const n = X.length, D = X[0].length, mu = new Float64Array(D); for (const r of X) for (let j = 0; j < D; j++) mu[j] += r[j] / n; return { Xc: X.map(r => r.map((x, j) => x - mu[j])), mu: Array.from(mu) }; }
  // top-k principal axes of X (n×D) without forming D×D when D is large: power iteration on X^T X with deflation
  function pcaTop(X, k, r) { const { Xc, mu } = center(X); const n = Xc.length, D = Xc[0].length; k = Math.min(k, D, n - 1);
    let axes = [], values = [];
    if (D <= 40) { const C = Array.from({ length: D }, () => Array(D).fill(0)); for (const row of Xc) for (let i = 0; i < D; i++) for (let j = 0; j < D; j++) C[i][j] += row[i] * row[j] / Math.max(1, n - 1); const e = jacobiEig(C); axes = e.vectors.slice(0, k); values = e.values; }
    else { const rr = r || mulberry32(1); const tot = Xc.reduce((s, row) => s + row.reduce((a, x) => a + x * x, 0), 0) / Math.max(1, n - 1);
      for (let a = 0; a < k; a++) { let v = Array.from({ length: D }, () => gauss(rr)); for (let it = 0; it < 40; it++) { const w = new Float64Array(D); for (const row of Xc) { let dot = 0; for (let j = 0; j < D; j++) dot += row[j] * v[j]; for (let j = 0; j < D; j++) w[j] += row[j] * dot; }
          for (const u of axes) { let d2 = 0; for (let j = 0; j < D; j++) d2 += w[j] * u[j]; for (let j = 0; j < D; j++) w[j] -= d2 * u[j]; }
          let nrm = 0; for (let j = 0; j < D; j++) nrm += w[j] * w[j]; nrm = Math.sqrt(nrm) || 1; v = Array.from(w, x => x / nrm); }
        let lam = 0; for (const row of Xc) { let dot = 0; for (let j = 0; j < D; j++) dot += row[j] * v[j]; lam += dot * dot; } values.push(lam / Math.max(1, n - 1)); axes.push(v); }
      values.push(Math.max(0, tot - values.reduce((a, b) => a + b, 0))); }
    // sign convention (determinism across the Jacobi / power-iteration paths): largest-|component| of each axis is positive
    axes = axes.map(a => { let m = 0; for (let j = 1; j < a.length; j++) if (Math.abs(a[j]) > Math.abs(a[m])) m = j; return a[m] < 0 ? a.map(x => -x) : a; });
    const proj = row => axes.map(a => a.reduce((s, aj, j) => s + aj * (row[j] - mu[j]), 0)); return { scores: X.map(proj), proj, values, axes, mu }; }
  // ---- §2.2 binarization R0 ----
  // threshold "median" = R0 (fixed column margins at ceil(N/2)); "zero" = Rabs (sign of the centered PCA score; column margins float)
  function binarizeR0(X, d, r, threshold) { threshold = threshold || "median"; const p = pcaTop(X, d, r); d = p.axes.length;
    const thr = Array.from({ length: d }, (_, j) => { if (threshold === "zero") return 0; const c = p.scores.map(row => row[j]).sort((a, b) => a - b); return c[Math.floor(c.length / 2)]; });
    const bits = p.scores.map(row => row.map((x, j) => x > thr[j] ? 1 : 0)); const name = threshold === "zero" ? "Rabs" : "R0";
    const rule = { rule: name, d, threshold, axes: p.axes.map(a => a.map(x => +x.toFixed(5))), thresholds: thr.map(x => +x.toFixed(5)) };
    return { bits, d, rule, rule_hash: hashStr(JSON.stringify(rule)), explained: p.values }; }
  // ---- §3 placement ----
  function zscore(B) { const n = B.length, d = B[0].length; const mu = Array(d).fill(0), sd = Array(d).fill(0); for (const r of B) for (let j = 0; j < d; j++) mu[j] += r[j] / n; for (const r of B) for (let j = 0; j < d; j++) sd[j] += (r[j] - mu[j]) ** 2 / n;
    const z = r => r.map((x, j) => (x - mu[j]) / (Math.sqrt(sd[j]) || 1)); return { Z: B.map(z), z }; }
  function lift(u0, v0, s) { const u = u0 * s, v = v0 * s, den = 1 + u * u + v * v; return [2 * u / den, 2 * v / den, (u * u + v * v - 1) / den]; }
  const chord = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  const geo = (a, b) => Math.acos(Math.max(-1, Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2])));
  function place(B) { const { Z, z } = zscore(B); const p = pcaTop(Z, 2); let maxR = 1e-9; for (const [u, v] of p.scores) maxR = Math.max(maxR, Math.hypot(u, v)); const s = 0.9 / maxR;
    const pts = p.scores.map(([u, v]) => lift(u, v, s)); const pole = lift(...p.proj(z(Array(B[0].length).fill(1))), s); const toS2 = bits => lift(...p.proj(z(bits)), s);
    const tot = p.values.reduce((a, b) => a + Math.max(0, b), 0) || 1; return { pts, pole, gaps: pts.map(q => chord(q, pole)), toS2, pc12: (Math.max(0, p.values[0]) + Math.max(0, p.values[1])) / tot }; }
  function V2(B) { const { Z } = zscore(B); const d = Z[0].length, n = Z.length; const C = Array.from({ length: d }, () => Array(d).fill(0)); for (const r of Z) for (let i = 0; i < d; i++) for (let j = 0; j < d; j++) C[i][j] += r[i] * r[j] / Math.max(1, n - 1); const ev = jacobiEig(C).values; return (Math.max(0, ev[0]) + Math.max(0, ev[1])) / d; }
  // ---- §4.3 curveball trades (Lean §8) ----
  function curveballDraw(B, trades, r, cert) { const M = B.map(x => x.slice()); const n = M.length, d = M[0].length; const rs = M.map(x => x.reduce((a, b) => a + b, 0)), cs = Array.from({ length: d }, (_, j) => M.reduce((a, x) => a + x[j], 0));
    let done = 0, tries = 0; while (done < trades && tries < trades * 40) { tries++; const i = Math.floor(r() * n), j = Math.floor(r() * n), a = Math.floor(r() * d), b = Math.floor(r() * d); if (i === j || a === b) continue;
      if (M[i][a] === 1 && M[i][b] === 0 && M[j][a] === 0 && M[j][b] === 1) { M[i][a] = 0; M[i][b] = 1; M[j][a] = 1; M[j][b] = 0; done++; } }
    const rs2 = M.map(x => x.reduce((a, b) => a + b, 0)), cs2 = Array.from({ length: d }, (_, j) => M.reduce((a, x) => a + x[j], 0));
    cert.rowOk = cert.rowOk && rs.every((v, i) => v === rs2[i]); cert.colOk = cert.colOk && cs.every((v, j) => v === cs2[j]); cert.trades += done; return M; }
  // ---- §4.1 atoms (Lean §1–3) ----
  function atomEdges(B, P) { const d = B[0].length; return B.map((bits, i) => { const dpre = P.gaps[i]; let best = { bits, dist: dpre, flip: -1 };
    for (let j = 0; j < d; j++) if (bits[j] === 0) { const nb = bits.slice(); nb[j] = 1; const dist = chord(P.toS2(nb), P.pole); if (dist < best.dist) best = { bits: nb, dist, flip: j }; }
    return { i, flip: best.flip, delta: dpre - best.dist, dk: best.flip < 0 ? 0 : 1, to: best.flip < 0 ? P.pts[i] : P.toS2(best.bits) }; }); }
  // ---- §4.2 compass (Lean §7) ----
  const logC = (n, k) => { let s = 0; for (let i = 1; i <= k; i++) s += Math.log(n - k + i) - Math.log(i); return s; };
  function compass(Phi, d, T, steps, r) { const F = k => Phi[k] - T * logC(d, k); let k = Math.floor(d / 2); const occ = Array(d + 1).fill(0), up = Array(d).fill(0), dn = Array(d).fill(0); let acc = 0, maxdk = 0;
    for (let s = 0; s < steps; s++) { const dir = r() < 0.5 ? 1 : -1; const k2 = k + dir; if (k2 < 0 || k2 > d) { occ[k]++; continue; } const alpha = Math.min(1, Math.exp(-(F(k2) - F(k)) / T));
      if (r() < alpha) { if (dir > 0) up[k]++; else dn[k2]++; maxdk = Math.max(maxdk, Math.abs(k2 - k)); k = k2; acc++; } occ[k]++; }
    const w = Array.from({ length: d + 1 }, (_, k) => Math.exp(-F(k) / T)); const Zs = w.reduce((a, b) => a + b, 0); const pi = w.map(x => x / Zs);
    const flux = up.map((u, k) => ({ k, up: u, down: dn[k], z: (u - dn[k]) / (Math.sqrt(u + dn[k]) || 1) }));
    return { T, steps, pi: pi.map(x => +x.toFixed(4)), kmean_analytic: pi.reduce((s, p, k) => s + p * k, 0), kmean_empirical: occ.reduce((s, c, k) => s + (c / steps) * k, 0), acceptance: acc / steps, maxdk, maxFluxZ: Math.max(...flux.map(f => Math.abs(f.z))) }; }
  function crossover(Phi, d) { const arg = T => { let b = 0, bv = -1e9; for (let k = 0; k <= d; k++) { const v = -(Phi[k] - T * logC(d, k)) / T; if (v > bv) { bv = v; b = k; } } return b; }; let lo = 1e-4, hi = 5; if (arg(lo) !== d) return null; for (let i = 0; i < 60; i++) { const m = (lo + hi) / 2; if (arg(m) === d) lo = m; else hi = m; } return (lo + hi) / 2; }
  // ---- §4.4 slerp + defocus (Lean §6) ----
  function slerp(p, q, t) { const c = Math.max(-1, Math.min(1, p[0] * q[0] + p[1] * q[1] + p[2] * q[2])); const O = Math.acos(c); if (O < 1e-9) return p; const a = Math.sin((1 - t) * O) / Math.sin(O), b = Math.sin(t * O) / Math.sin(O); return [a * p[0] + b * q[0], a * p[1] + b * q[1], a * p[2] + b * q[2]]; }
  function sh([x, y, z]) { return [0.28209479, 0.48860251 * y, 0.48860251 * z, 0.48860251 * x, 1.09254843 * x * y, 1.09254843 * y * z, 0.31539157 * (3 * z * z - 1), 1.09254843 * x * z, 0.54627422 * (x * x - y * y), 0.59004359 * y * (3 * x * x - y * y), 2.89061144 * x * y * z, 0.45704580 * y * (5 * z * z - 1), 0.37317633 * z * (5 * z * z - 3), 0.45704580 * x * (5 * z * z - 1), 1.44530572 * z * (x * x - y * y), 0.59004359 * x * (x * x - 3 * y * y)]; }
  function parsevalShares(pts) { const m = Array(16).fill(0); for (const p of pts) { const b = sh(p); for (let i = 0; i < 16; i++) m[i] += b[i] / pts.length; } const E = [m[0] ** 2, 0, 0, 0]; for (let i = 1; i < 4; i++) E[1] += m[i] ** 2; for (let i = 4; i < 9; i++) E[2] += m[i] ** 2; for (let i = 9; i < 16; i++) E[3] += m[i] ** 2; const tot = E.reduce((a, b) => a + b, 0) || 1; return E.map(e => e / tot); }
  const heatExp = l => l * (l + 1);
  // ---- synthetic cloud for demos ----
  function synth(N, D, seed) { const r = mulberry32(seed); const centers = [0, 1, 2].map(() => Array.from({ length: D }, () => gauss(r) * 2)); return Array.from({ length: N }, (_, i) => centers[i % 3].map((m, j) => m + gauss(r) * (j < 6 ? 0.6 : 1.4))); }
  // ---- the map ----
  function runMap(X, opts) { opts = opts || {}; const N = X.length, D = X[0].length; const seed = opts.seed ?? 20260906, T = opts.T ?? 0.05, K = Math.min(200, opts.K ?? 100), dReq = Math.min(24, opts.d ?? 9); const labels = opts.labels;
    const certs = []; const cert = (cls, theorem, ok, detail) => certs.push({ class: cls, theorem, ok: !!ok, detail });
    const r = mulberry32(seed);
    const keys = X.map((v, i) => ({ ordinal: i, hash: hashVec(v), label: labels ? labels[i] : undefined }));
    const threshold = opts.threshold === "zero" ? "zero" : "median"; const { bits, d, rule, rule_hash } = binarizeR0(X, dReq, r, threshold);
    const cls = new Map(); bits.forEach(b => { const k = b.join(""); cls.set(k, (cls.get(k) || 0) + 1); }); const largest = Math.max(...cls.values());
    cert("identity", "keyed-row injectivity (D6)", new Set(keys.map(k => k.ordinal)).size === N, `ordinal is the injective key; content hashes ${new Set(keys.map(k => k.hash)).size}/${N} distinct`);
    const P = place(bits); const ks = bits.map(b => b.reduce((a, x) => a + x, 0));
    const Phi = Array.from({ length: d + 1 }, (_, k) => { const g = P.gaps.filter((_, i) => ks[i] === k); return g.length ? g.reduce((a, b) => a + b, 0) / g.length : NaN; });
    const filled = []; for (let k = 0; k <= d; k++) if (Number.isNaN(Phi[k])) { filled.push(k); let lo = k - 1, hi = k + 1; while (lo >= 0 && Number.isNaN(Phi[lo])) lo--; while (hi <= d && Number.isNaN(Phi[hi])) hi++; Phi[k] = lo < 0 ? Phi[hi] : hi > d ? Phi[lo] : Phi[lo] + (Phi[hi] - Phi[lo]) * (k - lo) / (hi - lo); }
    const drops = Phi.slice(0, d).map((p, k) => p - Phi[k + 1]); const sumDrops = drops.reduce((a, b) => a + b, 0);
    cert("identity", "phi_ladder_telescope (Lean §5)", Math.abs(sumDrops - (Phi[0] - Phi[d])) < 1e-9, `Σdrops=${sumDrops.toFixed(6)} vs Φ(0)−Φ(d)=${(Phi[0] - Phi[d]).toFixed(6)}${filled.length ? `; empty shells ${filled.join(",")} linearly interpolated (stated)` : ""}`);
    const v2 = V2(bits); cert("identity", "gate_rank_identity (Lean §4)", true, `V₂=${v2.toFixed(4)} ⇔ r̂=2/V₂=${(2 / v2).toFixed(2)} ${2 / v2 <= 5 ? "≤ 5" : "> 5"}; a rank test, not evidence`);
    const A = atomEdges(bits, P); const minDelta = Math.min(...A.map(a => a.delta)); let run = 0, mono = true; for (const dl of A.map(a => a.delta).sort((a, b) => b - a)) { if (run + dl < run - 1e-12) mono = false; run += dl; }
    cert("identity", "atom_delta_nonneg (Lean §1)", minDelta >= -1e-12, `${A.filter(a => a.flip >= 0).length}/${N} items have a strictly improving flip; min Δ=${minDelta.toExponential(2)}`);
    cert("identity", "quantization max|dk|=1 (compass)", A.every(a => a.dk <= 1), `max dk=${Math.max(...A.map(a => a.dk))}`);
    cert("identity", "corpus_sum_nonneg + cumulative_monotone (Lean §2–3)", mono && run >= 0, `ΣΔ=${run.toFixed(4)}, prefix sums monotone=${mono}`);
    const trades = 5 * N * d; const c8 = { rowOk: true, colOk: true, trades: 0 }; const rn = mulberry32(seed ^ 0x9e3779b9); const nulls = []; for (let k = 0; k < K; k++) nulls.push(V2(curveballDraw(bits, trades, rn, c8)));
    const E0 = nulls.reduce((a, b) => a + b, 0) / K, SD0 = Math.sqrt(nulls.reduce((a, b) => a + (b - E0) ** 2, 0) / (K - 1)); const admissible = SD0 >= 1e-3; const z = (v2 - E0) / SD0;
    const verdict = !admissible ? "not-tested (degenerate null)" : Math.abs(z) >= 3 ? (z > 0 ? "excluded" : "excluded (inverted)") : "not-excluded";
    cert("identity", "trade_preserves_rowSum (Lean §8)", c8.rowOk, `${c8.trades} trades over ${K} draws`); cert("identity", "trade_preserves_colSum (Lean §8)", c8.colOk, `${c8.trades} trades over ${K} draws`);
    cert("measurement", "membership: SD₀[V₂] ≥ 1e-3", admissible, `SD₀=${SD0.toExponential(3)}`);
    cert("measurement", "ΔV₂z vs fixed-margin null (exclusion-only)", admissible && Math.abs(z) >= 3, admissible ? `ΔV₂=${(v2 - E0).toFixed(4)}, z=${z.toFixed(2)} → ${verdict}` : "void (inadmissible coordinate)");
    const C = compass(Phi, d, T, 60000, mulberry32(seed + 7)); const Tx = crossover(Phi, d);
    cert("identity", "mh_flux_symm / detailed balance (Lean §7)", C.maxFluxZ <= 3, `max |z(J)| over rungs = ${C.maxFluxZ.toFixed(2)}`); cert("identity", "quantization on accepted moves", C.maxdk <= 1, `max|dk|=${C.maxdk}`);
    const worst = A.reduce((b, a) => a.delta > b.delta ? a : b, A[0]); const ts = [0, 0.1, 0.25, 0.5, 0.75, 1]; const rungs = ts.map(t => slerp(P.pts[worst.i], P.pole, t)); let monoG = true; for (let i = 1; i < rungs.length; i++) if (geo(rungs[i], P.pole) > geo(rungs[i - 1], P.pole) + 1e-9) monoG = false;
    cert("identity", "slerp bridge: geodesic to target non-increasing", monoG, `item ${worst.i} → pole, ${rungs.length} rungs`);
    const E = parsevalShares(P.pts); const decay = [0.05, 0.2, 1].map(t => ({ t, E: E.map((e, l) => e * Math.exp(-2 * heatExp(l) * t)) }));
    cert("identity", "heat_exponent_monotone (Lean §6)", [0, 1, 2, 3].every((l, i, a) => i === 0 || heatExp(a[i - 1]) < heatExp(l)), `ℓ(ℓ+1) = ${[0, 1, 2, 3].map(heatExp).join(",")}`);
    cert("identity", "heat_exp_dominates_hamming (Lean §14)", [1, 2, 3].every(l => l < heatExp(l)), "sphere penalty strictly harsher than H(d,2) for ℓ≥1");
    // ---- NSS ladder (L1..L5): 12 azimuthal sectors -> 12 NSS axes (same sectoring as sos-agent). Candidate ATOMIC actions
    //      (add one item / remove one item / change one bit) are inserted, the sphere is REFIT, and the effect on the pole,
    //      sector occupancy and isolation is MEASURED. Rungs are ranked by measured movement; one rung is the selected ideal.
    //      Direction is free: shift the pole or fill a gap. Nothing here is "toward the ideal pole" by fiat.
    const NSS_AXES = ["Audience", "Inputs", "Outputs", "Mode", "Assumption set", "Adjacent problems", "Failure modes", "Lifecycle", "Composition", "Knowledge sources", "Calibration", "Recursion"];
    const sectorOf = ([x, y]) => Math.min(11, Math.floor(((Math.atan2(y, x) + Math.PI) / (2 * Math.PI)) * 12));
    const sectorCounts = Array(12).fill(0); P.pts.forEach(p => sectorCounts[sectorOf(p)]++);
    const isolatedCount = (pts, rr = 0.095) => pts.filter((p, i) => !pts.some((q, j) => j !== i && chord(p, q) < rr)).length;
    const baseOcc = sectorCounts.filter(c => c > 0).length, baseIso = isolatedCount(P.pts);
    const measure = (B2) => { const P2 = place(B2); const sc = Array(12).fill(0); P2.pts.forEach(p => sc[sectorOf(p)]++); return { pole_shift_geodesic: +geo(P.pole, P2.pole).toFixed(4), occupied_sectors_delta: sc.filter(c => c > 0).length - baseOcc, isolated_delta: isolatedCount(P2.pts) - baseIso, pc12_delta: +(P2.pc12 - P.pc12).toFixed(4) }; };
    const scoreOf = (m) => +(m.occupied_sectors_delta * 1.0 - 0.5 * m.isolated_delta + m.pole_shift_geodesic).toFixed(4);
    const bitName = (j) => `bit ${j} (PCA axis ${j} ${threshold === "zero" ? "> 0" : "> median"})`;
    const nameOf = (i) => keys[i].label ? `#${i} "${String(keys[i].label).slice(0, 40)}"` : `#${i}`;
    const meanZ = P.pts.reduce((a, p) => a + p[2], 0) / N;
    const cands = [];
    // add: one item whose pattern lands in an empty (or thinnest) sector
    const patterns = []; if (d <= 12) { for (let m = 0; m < (1 << d); m++) patterns.push(Array.from({ length: d }, (_, j) => (m >> j) & 1)); } else { const rp = mulberry32(seed + 99); for (let m = 0; m < 2000; m++) patterns.push(Array.from({ length: d }, () => rp() < 0.5 ? 1 : 0)); }
    const patPts = patterns.map(b => P.toS2(b));
    const thin = sectorCounts.map((c, sIdx) => ({ sIdx, c })).sort((a, b) => a.c - b.c).slice(0, 4);
    for (const { sIdx, c } of thin) { const phi = -Math.PI + ((sIdx + 0.5) / 12) * 2 * Math.PI; const rr = Math.sqrt(Math.max(0, 1 - meanZ * meanZ)); const center = [rr * Math.cos(phi), rr * Math.sin(phi), meanZ];
      let bi = 0, bd = 1e9; patPts.forEach((q, i) => { const dd = geo(q, center); if (dd < bd) { bd = dd; bi = i; } }); const pat = patterns[bi]; const fill = 3;
      const m = measure(bits.concat(Array.from({ length: fill }, () => pat.slice()))); const on = pat.map((v, j) => v ? j : -1).filter(j => j >= 0), off = pat.map((v, j) => v ? -1 : j).filter(j => j >= 0);
      cands.push({ action: "add", axis: NSS_AXES[sIdx], sector: sIdx, sector_count: c, pattern: pat, fill_size: fill, delta: m, score: scoreOf(m),
        hypothesis: `an item covering ${on.length ? on.map(bitName).join(", ") : "no bits"} and not ${off.length ? "bits " + off.join(",") : "any other bit"} lands in the ${c === 0 ? "empty" : "thin (" + c + " item" + (c === 1 ? "" : "s") + ")"} '${NSS_AXES[sIdx]}' sector`,
        method: `insert ${fill} co-located synthetic copies of the pattern, refit PCA2 + stereographic lift, remeasure pole / sectors / isolation`,
        recommendation: `Add ${fill} item${fill > 1 ? "s" : ""} that ${on.length ? "cover " + on.map(bitName).join(" and ") : "cover none of the bits"}${off.length ? " but not bit" + (off.length > 1 ? "s " : " ") + off.join(", ") : ""}. That pattern lands in the ${c === 0 ? "empty" : "thinly occupied"} '${NSS_AXES[sIdx]}' sector. Measured after refit: pole shifts ${m.pole_shift_geodesic} rad, occupied sectors ${m.occupied_sectors_delta >= 0 ? "+" : ""}${m.occupied_sectors_delta}, isolated points ${m.isolated_delta >= 0 ? "+" : ""}${m.isolated_delta}.` }); }
    // change: the strongest single-action atoms (flip one bit on one item)
    const topAtoms = A.filter(a => a.flip >= 0).sort((a, b) => b.delta - a.delta).slice(0, 3);
    for (const a of topAtoms) { const B2 = bits.map(r => r.slice()); B2[a.i][a.flip] = 1; const m = measure(B2);
      cands.push({ action: "change", axis: NSS_AXES[sectorOf(P.pts[a.i])], item: a.i, label: keys[a.i].label ?? null, flip_bit: a.flip, atom_delta: +a.delta.toFixed(4), delta: m, score: scoreOf(m),
        hypothesis: `turning ${bitName(a.flip)} on for item ${nameOf(a.i)} is its geodesic single-action atom (Δ=${a.delta.toFixed(3)} toward the pole)`,
        method: `flip the bit, refit, remeasure`, recommendation: `Change item ${nameOf(a.i)}: turn on ${bitName(a.flip)} (its single-action atom, Δ=${a.delta.toFixed(3)}, Lean §1). Measured after refit: pole shifts ${m.pole_shift_geodesic} rad, occupied sectors ${m.occupied_sectors_delta >= 0 ? "+" : ""}${m.occupied_sectors_delta}, isolated points ${m.isolated_delta >= 0 ? "+" : ""}${m.isolated_delta}.` }); }
    // remove: the most isolated item and the item farthest from the pole
    const nn = P.pts.map((p, i) => Math.min(...P.pts.map((q, j) => j === i ? Infinity : chord(p, q)))); const isoI = nn.indexOf(Math.max(...nn)); const farI = P.gaps.indexOf(Math.max(...P.gaps));
    for (const [i, why] of [[isoI, `the most isolated point (nearest neighbour ${nn[isoI].toFixed(3)} away)`], [farI, `the point farthest from the all-ones pole (gap ${P.gaps[farI].toFixed(3)})`]]) { if (i < 0 || N <= 10) continue; const B2 = bits.filter((_, k) => k !== i); const m = measure(B2);
      cands.push({ action: "remove", axis: NSS_AXES[sectorOf(P.pts[i])], item: i, label: keys[i].label ?? null, delta: m, score: scoreOf(m), hypothesis: `item ${nameOf(i)} is ${why}; removing it changes the fit`, method: `drop the row, refit, remeasure`,
        recommendation: `Remove item ${nameOf(i)}, ${why}, in the '${NSS_AXES[sectorOf(P.pts[i])]}' sector. Measured after refit: pole shifts ${m.pole_shift_geodesic} rad, occupied sectors ${m.occupied_sectors_delta >= 0 ? "+" : ""}${m.occupied_sectors_delta}, isolated points ${m.isolated_delta >= 0 ? "+" : ""}${m.isolated_delta}.` }); }
    const seen = new Set(); const ladder = cands.sort((a, b) => b.score - a.score).filter(c => { const k = c.action + ":" + (c.item ?? c.sector); if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 5)
      .map((c, r) => ({ rung: "L" + (r + 1), ...c, verdict: (Math.abs(c.delta.pole_shift_geodesic) > 0.02 || c.delta.occupied_sectors_delta !== 0 || c.delta.isolated_delta !== 0) ? "moves" : "no measurable move", caveat: "measured on this cloud under this rule; a re-embed with new text will land near, not on, the synthetic pattern" }));
    const idealReq = Number(opts.ideal); const idealIdx = Number.isInteger(idealReq) && idealReq >= 1 && idealReq <= ladder.length ? idealReq - 1 : 0;
    const nss = { axes: NSS_AXES, sector_counts: sectorCounts, empty_sectors: sectorCounts.map((c, i) => c === 0 ? NSS_AXES[i] : null).filter(Boolean), base: { occupied_sectors: baseOcc, isolated: baseIso }, ladder, ideal: ladder.length ? ladder[idealIdx].rung : null, recommendation: ladder.length ? ladder[idealIdx].recommendation : "no candidate actions (cloud too small)" };
    const shells = Array.from({ length: d + 1 }, (_, k) => ks.filter(x => x === k).length);
    return { version: "pointmap/0.1", rule_hash, rule: { rule: rule.rule, d, threshold, note: threshold === "zero" ? "top-d PCA axes of the centered cloud; bit_j = [score_j > 0] (sign rule; column margins float)" : "top-d PCA axes of the centered cloud; bit_j = [score_j > median_j] (column margins fixed at ceil(N/2))" }, seed, n: N, D, d, keys,
      classes: { count: cls.size, largest, unresolvable_pairs: [...cls.values()].reduce((s, c) => s + c * (c - 1) / 2, 0) },
      k: ks, pts: P.pts.map(p => p.map(x => +x.toFixed(5))), pole: P.pole.map(x => +x.toFixed(5)), gaps: P.gaps.map(x => +x.toFixed(5)), pc12: +P.pc12.toFixed(4), v2: +v2.toFixed(5),
      ladder: { Phi: Phi.map(x => +x.toFixed(4)), drops: drops.map(x => +x.toFixed(4)), interpolated_shells: filled }, shells,
      atoms: A.map(a => ({ i: a.i, flip: a.flip, delta: +a.delta.toFixed(5), to: a.to.map(x => +x.toFixed(5)) })),
      null: { kind: "curveball fixed-margin (Lean §8–10)", K, trades_per_draw: trades, E0: +E0.toFixed(5), SD0: +SD0.toFixed(6), z: admissible ? +z.toFixed(2) : null, admissible, verdict, stationary_law: "uniform on the fibre (Lean §10); irreducibility not checked at this N·d" },
      compass: { ...C, kmean_analytic: +C.kmean_analytic.toFixed(4), kmean_empirical: +C.kmean_empirical.toFixed(4), acceptance: +C.acceptance.toFixed(3), maxFluxZ: +C.maxFluxZ.toFixed(2), Tx: Tx === null ? null : +Tx.toFixed(6), wall: "property of a designed chain on a measured ladder, not of the cloud" },
      bridge: { i: worst.i, ts, rungs: rungs.map(p => p.map(x => +x.toFixed(5))) },
      nss,
      spectra: { S2_parseval: E.map(x => +x.toFixed(4)), decay: decay.map(o => ({ t: o.t, E: o.E.map(x => +x.toExponential(2)) })) },
      certificates: certs, summary: { identity_failures: certs.filter(c => c.class === "identity" && !c.ok).length, measurement_red: certs.filter(c => c.class === "measurement" && !c.ok).length } }; }
  // stated preprocessing for big-D clouds: top-k PCA scores (same sign convention), so servers with tight CPU budgets see k-D input
  function reduce(X, k, seed) { const p = pcaTop(X, k, mulberry32(seed ?? 1)); return { scores: p.scores.map(r => r.map(x => +x.toFixed(6))), explained: p.values.slice(0, k).map(x => +x.toFixed(6)) }; }
  return { runMap, synth, mulberry32, slerp, hashVec, hashStr, reduce };
})();
