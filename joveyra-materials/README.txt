JOVEYRA - FINAL APPROVED MATERIALS (one file per asset)
=======================================================

1-satellite/sat.mp4              Satellite hero loop. Full colour with the agreed
                                 lighting (not graded). 1920x1080, H.264, seamless loop.
2-flag/flag-alpha.mp4            Waving flag with a TRANSPARENT background, one file
                                 for every browser incl. Safari/iPhone. Top half =
                                 picture, bottom half = transparency mask. Must be
                                 played with flag-alpha.js (it looks wrong as a plain
                                 <video>). Floor widened, pole and hands complete.
2-flag/flag-alpha.js             The small player script for the file above.
2-flag/flag-demo.html            Open-in-browser test page (needs a web server).
3-dish/dish-2160.webp            Radio dish engraving, blue grade, 2160 px.
4-sr71-fire/sr71-fire.mp4        SR-71 afterburner loop, blue grade.
5-sr71-stills/sr71-tail-1080.webp  SR-71 tail view, blue grade.
5-sr71-stills/sr71-top-1080.webp   SR-71 top view, blue grade.
6-sr71-rotation/sr71-rotation-hevc.mp4  SR-71 rotation, original file.

HOW TO USE THE FLAG
-------------------
1. Upload flag-alpha.mp4 and flag-alpha.js to your site (same folder is easiest).
2. Where the flag should appear, paste:

     <canvas data-alpha-video="flag-alpha.mp4" style="width:100%"></canvas>

3. Once per page, before </body>, paste:

     <script src="flag-alpha.js" defer></script>

4. Size/position the canvas with CSS like an image; height follows the width.

If the MP4 is on a different domain or CDN than the page, that server must send
the header  Access-Control-Allow-Origin: *  or the flag will not draw.
The script pauses the video when it is off screen and shows a still frame for
visitors who have "reduce motion" turned on.
