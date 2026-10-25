JOVEYRA - FINAL AGREED MATERIALS
================================

Colour
  - 1-satellite : full colour (ATV orbit, agreed lighting). NOT graded.
  - everything else : the blue grade approved on the flag.
  - 6-sr71-rotation : the original Google Drive file, unchanged.

Folders
  1-satellite/      hero loop, Full HD 1920x1080, 25 fps, 30 s seamless loop
                    (desktop AND mobile files are both 1080p)
  2-flag/           flag on a TRANSPARENT background, floor widened left
                    and right (3200x1240). Nothing behind the men, flag,
                    pole, rocks and floor - place it on any page colour.
  3-dish/           radio dish engraving (800 / 1600 / 2160)
  4-sr71-fire/      SR-71 afterburner loop (closing section)
  5-sr71-stills/    SR-71 tail view + top view (800 / 1080)
  6-sr71-rotation/  SR-71 rotation, original (HEVC + AV1)

Formats
  Video : .webm (VP9)        - use first, smallest file
          .mp4  (H.264)      - fallback for Safari / older browsers
          -mobile.*          - mobile version (screens up to 900px)
          -poster.webp       - first frame, shown while the video loads
  Stills: .webp, quality 86, in several widths for srcset
          (flag stills keep their transparency)

Satellite
  <video muted playsinline loop autoplay poster="sat-poster.webp">
    <source src="sat-mobile.mp4" type="video/mp4" media="(max-width: 900px)">
    <source src="sat.webm" type="video/webm">
    <source src="sat.mp4" type="video/mp4">
  </video>

Flag (transparent)
  flag.webm / flag-mobile.webm carry real transparency (Chrome, Edge,
  Firefox, Android). Safari cannot play transparent WebM, so use
  flag-safari.mp4: the colour picture is the top half, the transparency
  mask the bottom half; the script below recombines them on a canvas.

  <div class="flag">
    <video id="flag" muted playsinline loop autoplay poster="flag-poster.webp">
      <source src="flag-mobile.webm" type="video/webm" media="(max-width: 900px)">
      <source src="flag.webm" type="video/webm">
    </video>
  </div>

  <script>
  (function () {
    var v = document.getElementById('flag');
    if (v.canPlayType('video/webm; codecs="vp9"')) return; // transparent webm works
    v.innerHTML = '<source src="flag-safari.mp4" type="video/mp4">';
    v.load();
    var c = document.createElement('canvas'), x = c.getContext('2d');
    c.className = v.className; v.style.display = 'none'; v.after(c);
    var b = document.createElement('canvas'), bx = b.getContext('2d', { willReadFrequently: true });
    function draw() {
      var w = v.videoWidth, h = v.videoHeight / 2;
      if (w) {
        if (c.width !== w) { c.width = b.width = w; c.height = h; b.height = h * 2; }
        bx.drawImage(v, 0, 0);
        var col = bx.getImageData(0, 0, w, h), m = bx.getImageData(0, h, w, h).data;
        for (var i = 3; i < col.data.length; i += 4) col.data[i] = m[i - 1];
        x.putImageData(col, 0, 0);
      }
      requestAnimationFrame(draw);
    }
    v.play(); requestAnimationFrame(draw);
  })();
  </script>
