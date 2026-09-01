/* nika sŭr-mã — interactive background
 *
 * The background is the render out of the TouchDesigner patch
 * "Smoke and Liquid Displacement Effects" (comp4), exported as a seamless
 * 12 s loop. The video is the picture; WebGL only adds the interaction —
 * the cursor displaces the footage, which is the same move the patch makes
 * internally. Without WebGL the <video> simply plays as it is.
 *
 * Set WARP to 0 below for the plain, untouched loop.
 */
(function () {
  'use strict';

  var WARP = 1;           // 0 disables the cursor displacement entirely
  var STRENGTH = 0.055;   // how far the cursor drags the image

  var video = document.getElementById('bgv');
  var canvas = document.getElementById('bg');
  if (!video) return;

  var reduced = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* On a phone the stylesheet shows #bgstill instead: never touch the video,
     or iOS lays its own transport controls over the page. */
  var still = window.matchMedia && window.matchMedia('(max-width: 760px)').matches;
  if (still) {
    video.removeAttribute('autoplay');
    video.preload = 'none';
    while (video.firstChild) video.removeChild(video.firstChild);
    video.load();
    return;
  }

  if (reduced) {
    video.removeAttribute('autoplay');
    video.pause();
    return;                     // poster frame only
  }

  function play() {
    var p = video.play();
    if (p && p.catch) p.catch(function () { /* blocked; poster stands in */ });
  }
  play();
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) video.pause(); else play();
  });

  /* Some browsers hold even a muted autoplay until the page is touched. */
  ['pointerdown', 'keydown', 'wheel', 'touchstart'].forEach(function (ev) {
    window.addEventListener(ev, function retry() {
      if (video.paused) play();
      if (!video.paused) {
        ['pointerdown', 'keydown', 'wheel', 'touchstart'].forEach(function (e2) {
          window.removeEventListener(e2, retry);
        });
      }
    }, { passive: true });
  });

  if (!WARP || !canvas) return;

  var gl = canvas.getContext('webgl2', {
    alpha: false, antialias: false, depth: false, stencil: false,
    powerPreference: 'low-power'
  });
  if (!gl) return;

  /* ---- shaders ------------------------------------------------------ */

  var VERT = `#version 300 es
  in vec2 aPos;
  out vec2 vUv;
  void main(){ vUv = aPos * 0.5 + 0.5; gl_Position = vec4(aPos, 0.0, 1.0); }`;

  var FRAG = `#version 300 es
  precision highp float;
  in vec2 vUv;
  out vec4 outColor;
  uniform sampler2D uTex;
  uniform vec2  uRes;        // canvas pixels
  uniform vec2  uVid;        // video pixels
  uniform vec2  uPointer;    // 0..1, y up
  uniform vec2  uPointerVel;
  uniform float uAmount;     // 0..1, decays when the pointer rests
  uniform float uStrength;
  uniform float uGrain;      // film grain, per page
  uniform float uTime;

  float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123); }

  void main(){
    // cover-fit the 16:9 loop into whatever shape the window is
    float ca = uRes.x / uRes.y;
    float va = uVid.x / uVid.y;
    vec2 scale = ca > va ? vec2(1.0, va / ca) : vec2(ca / va, 1.0);
    vec2 uv = (vUv - 0.5) * scale + 0.5;

    vec2 aspect = vec2(max(1.0, ca), max(1.0, 1.0 / ca));
    vec2 d = (vUv - uPointer) * aspect;
    float r = length(d);
    float fall = exp(-r * r * 7.0) * uAmount;

    vec2 warp = normalize(d + 1e-5) * fall * uStrength
              + uPointerVel * fall * 0.5;

    vec3 col = texture(uTex, clamp(uv + warp, 0.0, 1.0)).rgb;

    /* Grain is added here rather than baked into the file: it costs no
       bitrate, and it moves every frame the way real grain does. */
    if (uGrain > 0.0) {
      float n = hash(gl_FragCoord.xy + fract(uTime) * 137.0) - 0.5;
      col += n * uGrain;
    }

    outColor = vec4(col, 1.0);
  }`;

  function compile(type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.warn(gl.getShaderInfoLog(s));
      return null;
    }
    return s;
  }

  var v = compile(gl.VERTEX_SHADER, VERT);
  var f = compile(gl.FRAGMENT_SHADER, FRAG);
  if (!v || !f) return;
  var prog = gl.createProgram();
  gl.attachShader(prog, v);
  gl.attachShader(prog, f);
  gl.bindAttribLocation(prog, 0, 'aPos');
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    console.warn(gl.getProgramInfoLog(prog));
    return;
  }

  var vao = gl.createVertexArray();
  gl.bindVertexArray(vao);
  var buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0);
  gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

  var u = {};
  ['uTex', 'uRes', 'uVid', 'uPointer', 'uPointerVel', 'uAmount', 'uStrength',
   'uGrain', 'uTime']
    .forEach(function (n) { u[n] = gl.getUniformLocation(prog, n); });

  var grain = parseFloat(video.dataset.grain || '0') || 0;
  var started = performance.now();

  var tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

  /* ---- input -------------------------------------------------------- */

  var ptr = [0.5, 0.5], prev = [0.5, 0.5], vel = [0, 0], amount = 0;

  function point(x, y) {
    ptr = [x / window.innerWidth, 1 - y / window.innerHeight];
    amount = 1;
  }
  window.addEventListener('mousemove', function (e) { point(e.clientX, e.clientY); }, { passive: true });
  window.addEventListener('touchmove', function (e) {
    if (e.touches[0]) point(e.touches[0].clientX, e.touches[0].clientY);
  }, { passive: true });

  var wheel = 0;
  window.addEventListener('wheel', function (e) {
    wheel += Math.max(-1, Math.min(1, e.deltaY / 500));
    amount = 1;
  }, { passive: true });

  function resize() {
    var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    var w = Math.max(1, Math.round(window.innerWidth * dpr));
    var h = Math.max(1, Math.round(window.innerHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
  }
  window.addEventListener('resize', resize);
  resize();

  /* ---- loop --------------------------------------------------------- */

  var ready = false;

  function frame() {
    requestAnimationFrame(frame);
    resize();
    if (video.readyState < 2 || video.videoWidth === 0) return;

    if (!ready) {
      canvas.classList.add('on');
      ready = true;
    }

    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, video);

    vel = [(ptr[0] - prev[0]) * 2.2, (ptr[1] - prev[1]) * 2.2 - wheel * 0.06];
    prev = [ptr[0], ptr[1]];
    wheel *= 0.9;
    amount *= 0.955;

    gl.useProgram(prog);
    gl.bindVertexArray(vao);
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.uniform1i(u.uTex, 0);
    gl.uniform2f(u.uRes, canvas.width, canvas.height);
    gl.uniform2f(u.uVid, video.videoWidth, video.videoHeight);
    gl.uniform2fv(u.uPointer, ptr);
    gl.uniform2fv(u.uPointerVel, vel);
    gl.uniform1f(u.uAmount, amount);
    gl.uniform1f(u.uStrength, STRENGTH);
    gl.uniform1f(u.uGrain, grain);
    gl.uniform1f(u.uTime, (performance.now() - started) / 1000);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  requestAnimationFrame(frame);
})();
