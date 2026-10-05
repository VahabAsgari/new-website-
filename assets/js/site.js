(() => {
  const J = window.Jove;
  const reduce = J ? J.reduce : true;

  // soft inertial scroll
  let lenis = null;
  if (!reduce && window.Lenis) {
    lenis = new Lenis({ duration: 1.25, easing: (t) => 1 - Math.pow(1 - t, 3.2) });
    const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
    document.querySelectorAll('a[href^="#"]').forEach((a) => a.addEventListener("click", (e) => {
      const el = document.querySelector(a.getAttribute("href"));
      if (el) { e.preventDefault(); lenis.scrollTo(el); closeMenu(); }
    }));
  }

  // opening film: once per visit
  const film = document.getElementById("film");
  if (film && J && document.documentElement.classList.contains("film-on")) {
    film.hidden = false;
    try { sessionStorage.setItem("jv-film", "1"); } catch (e) {}
    J.film(film);
  } else if (film) film.remove();

  // plates develop through an ordered dither when they arrive
  if (J && !reduce) document.querySelectorAll("img[data-develop]").forEach(J.develop);

  // the moving plate at the end
  const sky = document.querySelector("canvas.sky");
  if (sky && J) J.jupiter(sky);

  // mobile menu
  const nav = document.querySelector(".nav");
  const btn = document.querySelector(".menu");
  function closeMenu() { if (nav) { nav.classList.remove("open"); btn && btn.setAttribute("aria-expanded", "false"); if (btn) btn.textContent = "Menu"; } }
  if (btn) btn.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    btn.setAttribute("aria-expanded", String(open));
    btn.textContent = open ? "Close" : "Menu";
  });
})();
