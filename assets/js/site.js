// Soft inertial scroll, deep-plane parallax, slow reveals.
(() => {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const nav = document.querySelector(".nav");

  // ---- smooth scroll (Lenis), long ease-out like a heavy object settling
  let lenis = null;
  if (!reduce && window.Lenis) {
    lenis = new Lenis({ duration: 1.5, easing: (t) => 1 - Math.pow(1 - t, 4), smoothWheel: true });
    document.querySelectorAll('a[href^="#"]').forEach((a) =>
      a.addEventListener("click", (e) => {
        const target = document.querySelector(a.getAttribute("href"));
        if (target) { e.preventDefault(); lenis.scrollTo(target, { offset: -72 }); nav.classList.remove("open"); }
      })
    );
  }

  // ---- parallax: images live on a farther plane than the words
  const layers = [...document.querySelectorAll("[data-depth]")];
  const vh = () => window.innerHeight;
  function frame(time) {
    if (lenis) lenis.raf(time);
    const y = window.scrollY;
    nav.classList.toggle("scrolled", y > 40);
    if (!reduce) {
      for (const el of layers) {
        const r = el.parentElement.getBoundingClientRect();
        if (r.bottom < -200 || r.top > vh() + 200) continue;
        const centre = r.top + r.height / 2 - vh() / 2;
        const d = parseFloat(el.dataset.depth);
        const s = 1 + Math.abs(d) * 0.12;
        el.style.transform = `translate3d(0, ${(-centre * d).toFixed(1)}px, 0) scale(${s})`;
      }
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  // ---- reveal on entry (once)
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
  }, { rootMargin: "0px 0px -12% 0px", threshold: 0.05 });
  document.querySelectorAll(".reveal, .develop").forEach((el) => io.observe(el));

  // ---- mobile menu
  const btn = document.querySelector(".menu-btn");
  if (btn) btn.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    btn.setAttribute("aria-expanded", String(open));
    btn.textContent = open ? "Close" : "Menu";
  });
})();
