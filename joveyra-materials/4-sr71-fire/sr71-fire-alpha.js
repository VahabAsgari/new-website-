/*
 * sr71-fire-alpha.js — plays a "stacked alpha" MP4 with a transparent background.
 *
 * The MP4 holds the picture in its top half and a black/white transparency
 * mask in its bottom half. This script draws both halves onto a <canvas>
 * with WebGL so the page shows through wherever the mask is black.
 * Works in Safari (Mac + iPhone), Chrome, Firefox and Edge. No libraries.
 *
 * Usage:
 *   <canvas data-alpha-video="sr71-fire-alpha.mp4" style="width:100%"></canvas>
 *   <script src="sr71-fire-alpha.js" defer></script>
 *
 * Optional attribute: data-poster="sr71-fire-poster.webp" — shown if WebGL is
 * unavailable. Call AlphaVideo(canvas, src) yourself for canvases added later.
 */
(function () {
  'use strict';

  var VERT =
    'attribute vec2 p;varying vec2 uv;' +
    'void main(){uv=vec2((p.x+1.)*.5,(1.-p.y)*.5);gl_Position=vec4(p,0.,1.);}';

  // Colour from the top half, mask from the bottom half; output premultiplied.
  var FRAG =
    'precision mediump float;uniform sampler2D t;varying vec2 uv;' +
    'void main(){vec3 c=texture2D(t,vec2(uv.x,uv.y*.5)).rgb;' +
    'float a=texture2D(t,vec2(uv.x,.5+uv.y*.5)).r;' +
    'gl_FragColor=vec4(c*a,a);}';

  function shader(gl, type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    return s;
  }

  function AlphaVideo(canvas, src) {
    var gl = canvas.getContext('webgl', { premultipliedAlpha: true, alpha: true }) ||
             canvas.getContext('experimental-webgl');
    if (!gl) {
      var poster = canvas.getAttribute('data-poster');
      if (poster) {
        var img = new Image();
        img.src = poster;
        img.alt = canvas.getAttribute('aria-label') || '';
        img.style.cssText = canvas.style.cssText;
        canvas.replaceWith(img);
      }
      return null;
    }

    var video = document.createElement('video');
    video.crossOrigin = 'anonymous';
    video.muted = true;
    video.defaultMuted = true;
    video.loop = true;
    video.autoplay = true;
    video.playsInline = true;
    video.setAttribute('muted', '');
    video.setAttribute('playsinline', '');
    video.setAttribute('webkit-playsinline', '');
    video.preload = 'auto';
    video.src = src;

    var prog = gl.createProgram();
    gl.attachShader(prog, shader(gl, gl.VERTEX_SHADER, VERT));
    gl.attachShader(prog, shader(gl, gl.FRAGMENT_SHADER, FRAG));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    var buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(prog, 'p');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

    var tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.clearColor(0, 0, 0, 0);

    // Keep the canvas buffer matched to its on-screen size × pixel density.
    function resize() {
      var w = video.videoWidth, h = video.videoHeight / 2;
      if (!w) return;
      if (!canvas.style.aspectRatio) canvas.style.aspectRatio = w + ' / ' + h;
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      var cw = Math.round((canvas.clientWidth || w) * dpr);
      var bw = Math.min(cw, w), bh = Math.round(bw * h / w);
      if (canvas.width !== bw || canvas.height !== bh) {
        canvas.width = bw;
        canvas.height = bh;
        gl.viewport(0, 0, bw, bh);
      }
    }

    function draw() {
      if (video.readyState >= 2) {
        resize();
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, video);
        gl.clear(gl.COLOR_BUFFER_BIT);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      }
      schedule();
    }

    var rvfc = 'requestVideoFrameCallback' in HTMLVideoElement.prototype;
    function schedule() {
      if (rvfc) video.requestVideoFrameCallback(draw);
      else requestAnimationFrame(draw);
    }

    window.addEventListener('resize', resize);
    video.addEventListener('loadeddata', draw, { once: true });

    // Pause when scrolled out of view to save battery.
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        entries[0].isIntersecting ? play() : video.pause();
      }).observe(canvas);
    }

    // Respect "reduce motion": show the first frame only.
    var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    function play() {
      if (still) return;
      var p = video.play();
      if (p && p.catch) p.catch(function () {});
    }
    if (still) video.addEventListener('loadeddata', function () { video.pause(); }, { once: true });
    play();

    return video;
  }

  window.AlphaVideo = AlphaVideo;

  function init() {
    var list = document.querySelectorAll('canvas[data-alpha-video]');
    for (var i = 0; i < list.length; i++) {
      if (!list[i].__alpha) {
        list[i].__alpha = true;
        AlphaVideo(list[i], list[i].getAttribute('data-alpha-video'));
      }
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
