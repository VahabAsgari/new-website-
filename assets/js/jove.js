// Jove — Jupiter and the four Medicean moons, drawn as data.
// Real orbital periods (days) and distances (Jupiter radii).
(() => {
  const MOONS = [
    { P: 1.769, a: 5.9 },   // Io
    { P: 3.551, a: 9.4 },   // Europa
    { P: 7.155, a: 15.0 },  // Ganymede
    { P: 16.689, a: 26.4 }, // Callisto
  ];
  const PHASE = [0.3, 2.1, 4.0, 5.2];
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const pos = (m, i, day) => Math.sin((2 * Math.PI * day) / m.P + PHASE[i]) * m.a;
  const ease = (t) => (t <= 0 ? 0 : t >= 1 ? 1 : 1 - Math.pow(1 - t, 3));
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  function fit(canvas) {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const r = canvas.getBoundingClientRect();
    canvas.width = Math.round(r.width * dpr);
    canvas.height = Math.round(r.height * dpr);
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, w: r.width, h: r.height };
  }

  // ------------------------------------------------------------------ opening film
  function film(root) {
    const canvas = root.querySelector("canvas");
    const mark = root.querySelector(".film-mark");
    const date = root.querySelector(".film-date");
    let { ctx, w, h } = fit(canvas);
    const onResize = () => ({ ctx, w, h } = fit(canvas));
    addEventListener("resize", onResize);
    const ink = getComputedStyle(root).color;
    const T = { notebook: 3.4, waves: 2.6, mark: 1.6 };
    const total = T.notebook + T.waves + T.mark;
    const nights = 12;
    const start = 7; // 7 January 1610
    let t0 = null, raf = 0, done = false;

    function finish() {
      if (done) return;
      done = true;
      cancelAnimationFrame(raf);
      root.classList.add("lift");
      document.documentElement.classList.remove("film-on");
      setTimeout(() => { root.remove(); removeEventListener("resize", onResize); }, 1400);
    }
    root.addEventListener("click", finish);
    addEventListener("keydown", (e) => { if (e.key === "Escape" || e.key === " ") finish(); }, { once: true });

    function frame(now) {
      if (t0 === null) t0 = now;
      const t = (now - t0) / 1000;
      ctx.clearRect(0, 0, w, h);
      ctx.strokeStyle = ink; ctx.fillStyle = ink;
      const unit = Math.min(w / 70, 13);
      const cx = w / 2;

      // 1. notebook rows: one per night
      const rowH = Math.min(34, (h * 0.62) / nights);
      const top = h / 2 - (rowH * nights) / 2;
      const p1 = clamp(t / T.notebook, 0, 1);
      const p2 = clamp((t - T.notebook) / T.waves, 0, 1);
      const shown = Math.floor(p1 * nights * 1.15);
      const collapse = ease(p2);
      ctx.globalAlpha = 1 - ease(clamp((t - T.notebook - T.waves * 0.55) / (T.waves * 0.45), 0, 1));
      for (let n = 0; n < Math.min(shown, nights); n++) {
        const y = top + n * rowH + rowH / 2;
        const yy = y + (h / 2 - y) * collapse;
        const fade = clamp((p1 * nights * 1.15 - n) * 1.5, 0, 1);
        ctx.globalAlpha *= 1; const a0 = ctx.globalAlpha;
        ctx.globalAlpha = a0 * fade * (1 - collapse * 0.85);
        ctx.lineWidth = 0.6;
        ctx.beginPath(); ctx.moveTo(cx - 30 * unit, yy); ctx.lineTo(cx + 30 * unit, yy); ctx.stroke();
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.arc(cx, yy, unit * 0.9, 0, Math.PI * 2); ctx.stroke();
        MOONS.forEach((m, i) => {
          const x = cx + pos(m, i, n) * unit;
          ctx.beginPath(); ctx.arc(x, yy, 2.1, 0, Math.PI * 2); ctx.fill();
        });
        ctx.globalAlpha = a0;
      }
      ctx.globalAlpha = 1;
      if (date) {
        const day = Math.min(start + Math.max(0, shown - 1), start + nights - 1);
        date.textContent = p2 > 0 ? "" : `Padua, ${day} January 1610`;
      }

      // 2. orbits seen edge-on become waves
      if (p2 > 0) {
        const wv = ease(clamp((t - T.notebook - 0.2) / T.waves, 0, 1));
        const fadeOut = 1 - ease(clamp((t - T.notebook - T.waves) / (T.mark * 0.8), 0, 1));
        const span = h * 0.9 * wv;
        MOONS.forEach((m, i) => {
          ctx.globalAlpha = fadeOut * (0.95 - i * 0.12);
          ctx.lineWidth = 1.1;
          ctx.beginPath();
          for (let k = 0; k <= 240; k++) {
            const f = k / 240;
            const day = (t - T.notebook) * 6 - f * 26;
            const x = cx + pos(m, i, day) * unit;
            const y = h / 2 - span / 2 + f * span;
            k ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
          }
          ctx.stroke();
        });
        ctx.globalAlpha = fadeOut;
        ctx.beginPath(); ctx.arc(cx, h / 2, unit * 0.9, 0, Math.PI * 2); ctx.stroke();
        ctx.globalAlpha = 1;
      }

      // 3. the mark
      const p3 = clamp((t - T.notebook - T.waves * 0.75) / T.mark, 0, 1);
      if (mark) mark.style.opacity = String(ease(p3));
      if (t > total + 0.4) return finish();
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);
  }

  // ------------------------------------------------------------------ Jupiter, engraved in code
  // The planet is shaded only with horizontal lines whose weight follows the light,
  // like a burin cut. The moons travel their real periods around it.
  function jupiter(canvas) {
    let { ctx, w, h } = fit(canvas);
    addEventListener("resize", () => ({ ctx, w, h } = fit(canvas)));
    const color = getComputedStyle(canvas).color;
    let visible = false, raf = 0;
    new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      if (visible && !raf) raf = requestAnimationFrame(draw);
    }).observe(canvas);
    const t0 = performance.now();

    function draw(now) {
      raf = 0;
      if (!visible) return;
      const t = (now - t0) / 1000;
      const day = reduce ? 3.2 : t * 0.35;
      ctx.clearRect(0, 0, w, h);
      ctx.strokeStyle = color; ctx.fillStyle = color;
      const R = Math.min(w * 0.24, h * 0.27);
      const cx = w * 0.5, cy = h * 0.36;
      const tilt = 0.16; // orbits seen almost edge-on
      // moons behind the planet first
      const moons = MOONS.map((m, i) => {
        const ang = (2 * Math.PI * day) / m.P + PHASE[i];
        const rr = R * (1.25 + m.a / 13);
        return { x: cx + Math.sin(ang) * rr, y: cy + Math.cos(ang) * rr * tilt, z: Math.cos(ang), rr, i };
      });
      // orbit ellipses
      ctx.lineWidth = 0.6; ctx.globalAlpha = 0.55;
      moons.forEach((m) => { ctx.beginPath(); ctx.ellipse(cx, cy, m.rr, m.rr * tilt, 0, 0, Math.PI * 2); ctx.stroke(); });
      ctx.globalAlpha = 1;
      const drawMoon = (m) => { ctx.beginPath(); ctx.arc(m.x, m.y, Math.max(2, R * 0.022), 0, Math.PI * 2); ctx.fill(); };
      moons.filter((m) => m.z < 0).forEach(drawMoon);
      // planet: clear disc then engrave
      ctx.save();
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.clip();
      ctx.globalCompositeOperation = "destination-out";
      ctx.fillRect(cx - R, cy - R, 2 * R, 2 * R);
      ctx.globalCompositeOperation = "source-over";
      const gap = Math.max(4, R / 40);
      const lx = -0.55, ly = -0.45; // light from upper left
      for (let y = -R; y <= R; y += gap) {
        const lat = y / R;
        const half = Math.sqrt(Math.max(0, 1 - lat * lat)) * R;
        const band = 0.5 + 0.5 * Math.sin(lat * 15.5 + Math.sin(lat * 5) * 1.6 + t * 0.05);
        let cur = -1, px = 0, py = 0;
        for (let x = -half; x <= half; x += 2) {
          const nx = x / R, ny = lat, nz = Math.sqrt(Math.max(0, 1 - nx * nx - ny * ny));
          const light = clamp(nx * lx + ny * ly + nz * 0.75, 0, 1);
          const wgt = clamp(Math.pow(light, 0.8) * 3.4 * (0.42 + 0.58 * band), 0.05, 3.2);
          const yy = cy + y + Math.sin((x / R) * 7 + lat * 30 + t * 0.15) * gap * 0.12;
          const b = wgt < 0.14 ? 0 : Math.round(wgt * 4) / 4;
          if (b !== cur) {
            if (cur > 0) { ctx.lineTo(cx + x, yy); ctx.stroke(); }
            cur = b;
            if (b > 0) { ctx.beginPath(); ctx.lineWidth = b; ctx.moveTo(cx + x, yy); }
          } else if (b > 0) ctx.lineTo(cx + x, yy);
          px = x; py = yy;
        }
        if (cur > 0) ctx.stroke();
      }
      ctx.restore();
      ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.stroke();
      moons.filter((m) => m.z >= 0).forEach(drawMoon);
      if (!reduce) raf = requestAnimationFrame(draw);
    }
  }

  // ------------------------------------------------------------------ dithered development
  // Plates appear the way a halftone resolves: an ordered (Bayer) threshold sweeps in.
  const BAYER = [0, 32, 8, 40, 2, 34, 10, 42, 48, 16, 56, 24, 50, 18, 58, 26, 12, 44, 4, 36, 14, 46, 6, 38, 60, 28, 52, 20, 62, 30, 54, 22, 3, 35, 11, 43, 1, 33, 9, 41, 51, 19, 59, 27, 49, 17, 57, 25, 15, 47, 7, 39, 13, 45, 5, 37, 63, 31, 55, 23, 61, 29, 53, 21];
  function develop(img) {
    const wrap = img.parentElement;
    const c = document.createElement("canvas");
    c.className = "dither";
    wrap.appendChild(c);
    const run = () => {
      const r = img.getBoundingClientRect();
      const px = 3; // dither cell size in CSS px
      const cw = Math.ceil(r.width / px), ch = Math.ceil(r.height / px);
      c.width = cw; c.height = ch;
      const ctx = c.getContext("2d");
      const start = performance.now(), dur = 1100;
      const step = (now) => {
        const p = clamp((now - start) / dur, 0, 1);
        const k = Math.floor(ease(p) * 65);
        const id = ctx.createImageData(cw, ch);
        const col = getComputedStyle(c).color.match(/\d+/g).map(Number);
        for (let y = 0; y < ch; y++) for (let x = 0; x < cw; x++) {
          const i = (y * cw + x) * 4;
          const on = BAYER[(y & 7) * 8 + (x & 7)] >= k;
          id.data[i] = col[0]; id.data[i + 1] = col[1]; id.data[i + 2] = col[2]; id.data[i + 3] = on ? 255 : 0;
        }
        ctx.putImageData(id, 0, 0);
        if (p < 1) requestAnimationFrame(step); else c.remove();
      };
      requestAnimationFrame(step);
    };
    const go = () => (img.complete ? run() : img.addEventListener("load", run, { once: true }));
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { io.disconnect(); go(); } }, { threshold: 0.25 });
    io.observe(wrap);
  }

  window.Jove = { film, jupiter, develop, reduce };
})();
