/* Joveyra: smooth scroll, the nav, the menu, and the films. Nothing else moves. */
(function () {
  "use strict";
  var root = document.documentElement;
  var still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  root.classList.add("js");

  function store(k, v) { try { sessionStorage.setItem(k, v); } catch (e) {} }

  /* ------------------------------------------------------------ menu */
  var menu = document.querySelector(".menu");
  function setMenu(open) {
    root.classList.toggle("menu-open", open);
    if (menu) {
      menu.setAttribute("aria-expanded", open ? "true" : "false");
      menu.textContent = open ? "Close" : "Menu";
    }
  }
  if (menu) menu.addEventListener("click", function () { setMenu(!root.classList.contains("menu-open")); });
  addEventListener("keydown", function (e) { if (e.key === "Escape") setMenu(false); });

  /* ------------------------------------------------------------ scroll */
  var lenis = null;
  if (!still && window.Lenis) {
    lenis = new Lenis({ duration: 1.15, smoothWheel: true });
    (function raf(t) { lenis.raf(t); requestAnimationFrame(raf); })(performance.now());
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) return;
    var id = a.getAttribute("href");
    var el = id.length > 1 && document.querySelector(id);
    setMenu(false);
    if (!el) return;
    e.preventDefault();
    if (lenis) lenis.scrollTo(el, { offset: 0 });
    else el.scrollIntoView({ behavior: still ? "auto" : "smooth" });
  });

  var nav = document.querySelector(".nav");
  function onScroll() { if (nav) nav.classList.toggle("solid", scrollY > 40); }
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ------------------------------------------------------------ films */
  function load(v) {
    if (v.dataset.loaded) return;
    v.querySelectorAll("source[data-src]").forEach(function (s) { s.src = s.dataset.src; });
    v.dataset.loaded = "1";
    v.load();
  }
  function play(v) {
    if (still) return Promise.reject();
    var p = v.play();
    return p && p.catch ? p : Promise.resolve();
  }

  var loop = document.querySelector(".hero .v-loop");
  var open = document.querySelector(".hero .v-open");
  var skip = document.querySelector(".hero .skip");

  if (open && root.classList.contains("film-on")) {
    var done = false;
    var finish = function () {
      if (done) return;
      done = true;
      if (loop) { try { loop.currentTime = 0; } catch (e) {} play(loop).catch(function () {}); }
      open.classList.add("gone");
      root.classList.remove("film-on");
      store("jv-film", "1");
      setTimeout(function () { open.pause(); }, 1600);
    };
    load(open);
    open.addEventListener("ended", finish);
    open.addEventListener("error", finish, true);
    if (skip) skip.addEventListener("click", finish);
    play(open).catch(finish);
    setTimeout(function () { if (!done && open.currentTime === 0) finish(); }, 4000);
  } else {
    root.classList.remove("film-on");
    if (open) open.remove();
    if (skip) skip.remove();
    if (loop) play(loop).catch(function () {});
  }

  /* every other film plays only while it is on screen */
  var lazy = document.querySelectorAll("video[data-lazy]");
  if ("IntersectionObserver" in window && lazy.length) {
    var vo = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        var v = e.target;
        if (e.isIntersecting) { load(v); play(v).catch(function () {}); }
        else if (!v.paused) v.pause();
      });
    }, { rootMargin: "200px 0px" });
    lazy.forEach(function (v) { vo.observe(v); });
  }
  if (loop && "IntersectionObserver" in window) {
    new IntersectionObserver(function (es) {
      if (root.classList.contains("film-on")) return;
      es.forEach(function (e) {
        if (e.isIntersecting) play(loop).catch(function () {});
        else loop.pause();
      });
    }).observe(loop);
  }

  /* plates settle as they arrive */
  var settle = document.querySelectorAll(".settle");
  if ("IntersectionObserver" in window && !still) {
    var so = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); so.unobserve(e.target); } });
    }, { threshold: 0.12 });
    settle.forEach(function (el) { so.observe(el); });
  } else {
    settle.forEach(function (el) { el.classList.add("in"); });
  }
})();
