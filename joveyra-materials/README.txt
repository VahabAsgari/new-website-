JOVEYRA - FINAL AGREED MATERIALS
================================

Colour
  - 1-satellite : full colour (ATV orbit, agreed lighting). NOT graded.
  - everything else : the blue grade approved on the flag.
  - 6-sr71-rotation : the original Google Drive file, unchanged.

Folders
  1-satellite/      hero loop, 1920x1080, 25 fps, 30 s seamless loop
  2-flag/           flag stills (800 / 1600 / 1800) + flag video loop
  3-dish/           radio dish engraving (800 / 1600 / 2160)
  4-sr71-fire/      SR-71 afterburner loop (closing section)
  5-sr71-stills/    SR-71 tail view + top view (800 / 1080)
  6-sr71-rotation/  SR-71 rotation, original (HEVC + AV1)

Formats
  Video : .webm (VP9)        - use first, smallest file
          .mp4  (H.264)      - fallback for Safari / older browsers
          -1280.mp4          - mobile version (screens up to 900px)
          -poster.webp       - first frame, shown while the video loads
  Stills: .webp, quality 86, in several widths for srcset

Usage in HTML
  <video muted playsinline loop autoplay poster="sat-poster.webp">
    <source src="sat-1280.mp4" type="video/mp4" media="(max-width: 900px)">
    <source src="sat.webm" type="video/webm">
    <source src="sat.mp4" type="video/mp4">
  </video>
