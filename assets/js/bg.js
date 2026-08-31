/* nika sŭr-mã — interactive background
 *
 * A smoke / liquid-displacement field in blue, after the TouchDesigner patch:
 * a half-resolution velocity + dye buffer is advected and stirred by curl
 * noise, the pointer and the scroll wheel push into it, and a second pass
 * uses that field to domain-warp fbm noise into smoke.
 *
 * Degrades to the static gradient painted on #bg by the stylesheet when
 * WebGL2 or float render targets are unavailable.
 */
(function () {
  'use strict';

  var canvas = document.getElementById('bg');
  if (!canvas) return;

  var reduced = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var gl = canvas.getContext('webgl2', {
    alpha: false, antialias: false, depth: false, stencil: false,
    powerPreference: 'low-power', preserveDrawingBuffer: false
  });
  if (!gl || !gl.getExtension('EXT_color_buffer_float')) return;
  gl.getExtension('OES_texture_float_linear');

  /* ---- shaders ------------------------------------------------------ */

  var VERT = `#version 300 es
  in vec2 aPos;
  out vec2 vUv;
  void main(){ vUv = aPos * 0.5 + 0.5; gl_Position = vec4(aPos, 0.0, 1.0); }`;

  var NOISE = `
  float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123); }
  float vnoise(vec2 p){
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1,0)), f.x),
               mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), f.x), f.y);
  }
  float fbm(vec2 p){
    float a = 0.5, s = 0.0;
    for (int i = 0; i < 5; i++){ s += a * vnoise(p); p *= 2.03; a *= 0.5; }
    return s;
  }
  vec2 curl(vec2 p){
    float e = 0.09;
    return vec2( fbm(p + vec2(0.0, e)) - fbm(p - vec2(0.0, e)),
                -fbm(p + vec2(e, 0.0)) + fbm(p - vec2(e, 0.0)) ) / (2.0 * e);
  }`;

  var SIM = `#version 300 es
  precision highp float;
  in vec2 vUv;
  out vec4 outColor;
  uniform sampler2D uState;
  uniform vec2  uAspect;
  uniform float uTime, uDt;
  uniform vec2  uPointer, uPointerVel;
  uniform float uPointerOn;
  ` + NOISE + `
  void main(){
    vec2 uv = vUv;
    vec4 s = texture(uState, uv);
    vec2 vel = s.xy;

    vel += curl(uv * 3.1 + vec2(0.0, uTime * 0.035)) * 0.055 * uDt;

    vec2 adv = texture(uState, uv - vel * uDt).xy;
    float dye = texture(uState, uv - vel * uDt).z;
    vel = mix(vel, adv, 0.9);

    float d = distance(uv * uAspect, uPointer * uAspect);
    float g = exp(-d * d * 190.0) * uPointerOn;
    vel += uPointerVel * g * 1.1;
    dye += g * 0.9 * uDt * 60.0 * 0.05;

    dye += 0.0022 * fbm(uv * 4.0 + vec2(uTime * 0.02, -uTime * 0.03));

    vel *= 0.9935;
    dye *= 0.986;

    outColor = vec4(clamp(vel, -3.0, 3.0), clamp(dye, 0.0, 1.7), 1.0);
  }`;

  var DRAW = `#version 300 es
  precision highp float;
  in vec2 vUv;
  out vec4 outColor;
  uniform sampler2D uState;
  uniform vec2  uAspect;
  uniform float uTime, uIntensity;
  ` + NOISE + `
  void main(){
    vec2 uv = vUv;
    vec4 s = texture(uState, uv);
    vec2 v = s.xy;
    float dye = s.z;

    vec2 w = uv * vec2(2.7, 2.7) + v * 0.85 + vec2(0.0, -uTime * 0.014);
    float n = fbm(w + fbm(w * 1.7 + uTime * 0.018) * 0.9);
    float smoke = n * 0.8 + dye * 0.85;

    vec3 deep = vec3(0.020, 0.036, 0.064);
    vec3 mid  = vec3(0.043, 0.153, 0.300);
    vec3 hi   = vec3(0.404, 0.706, 0.976);

    vec3 col = mix(deep, mid, smoothstep(0.10, 0.72, smoke));
    col = mix(col, hi, smoothstep(0.70, 1.25, smoke + dye * 0.55) * 0.8);

    float vig = smoothstep(1.30, 0.30, length((uv - 0.5) * uAspect) * 1.30);
    col *= mix(0.55, 1.0, vig);
    col += (hash(gl_FragCoord.xy + uTime) - 0.5) * 0.010;

    outColor = vec4(col * uIntensity, 1.0);
  }`;

  /* ---- plumbing ----------------------------------------------------- */

  function compile(type, src) {
    var sh = gl.createShader(type);
    gl.shaderSource(sh, src);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
      console.warn(gl.getShaderInfoLog(sh));
      return null;
    }
    return sh;
  }

  function program(fragSrc) {
    var v = compile(gl.VERTEX_SHADER, VERT);
    var f = compile(gl.FRAGMENT_SHADER, fragSrc);
    if (!v || !f) return null;
    var p = gl.createProgram();
    gl.attachShader(p, v);
    gl.attachShader(p, f);
    gl.bindAttribLocation(p, 0, 'aPos');
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
      console.warn(gl.getProgramInfoLog(p));
      return null;
    }
    return p;
  }

  var simProg = program(SIM);
  var drawProg = program(DRAW);
  if (!simProg || !drawProg) return;

  var vao = gl.createVertexArray();
  gl.bindVertexArray(vao);
  var buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0);
  gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

  function uniforms(p, names) {
    var o = {};
    for (var i = 0; i < names.length; i++) o[names[i]] = gl.getUniformLocation(p, names[i]);
    return o;
  }
  var uSim = uniforms(simProg, ['uState', 'uAspect', 'uTime', 'uDt', 'uPointer', 'uPointerVel', 'uPointerOn']);
  var uDraw = uniforms(drawProg, ['uState', 'uAspect', 'uTime', 'uIntensity']);

  function target(w, h) {
    var tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, w, h, 0, gl.RGBA, gl.HALF_FLOAT, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    var fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    return { tex: tex, fbo: fbo, w: w, h: h };
  }

  var a = null, b = null, simW = 0, simH = 0, aspect = [1, 1];

  function resize() {
    var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    var w = Math.max(1, Math.round(window.innerWidth * dpr));
    var h = Math.max(1, Math.round(window.innerHeight * dpr));
    if (canvas.width === w && canvas.height === h) return;
    canvas.width = w;
    canvas.height = h;
    aspect = [Math.max(1, w / h), Math.max(1, h / w)];

    var scale = Math.min(1, 420 / Math.max(w, h));
    simW = Math.max(8, Math.round(w * scale));
    simH = Math.max(8, Math.round(h * scale));
    if (a) { gl.deleteTexture(a.tex); gl.deleteFramebuffer(a.fbo); }
    if (b) { gl.deleteTexture(b.tex); gl.deleteFramebuffer(b.fbo); }
    a = target(simW, simH);
    b = target(simW, simH);
    for (var i = 0; i < 2; i++) {
      gl.bindFramebuffer(gl.FRAMEBUFFER, i ? b.fbo : a.fbo);
      gl.viewport(0, 0, simW, simH);
      gl.clearColor(0, 0, 0, 1);
      gl.clear(gl.COLOR_BUFFER_BIT);
    }
  }

  /* ---- input -------------------------------------------------------- */

  var ptr = [0.5, 0.5], ptrPrev = [0.5, 0.5], ptrVel = [0, 0], ptrOn = 0;

  function point(x, y) {
    ptr = [x / window.innerWidth, 1 - y / window.innerHeight];
    ptrOn = 1;
  }
  window.addEventListener('mousemove', function (e) { point(e.clientX, e.clientY); }, { passive: true });
  window.addEventListener('touchmove', function (e) {
    if (e.touches[0]) point(e.touches[0].clientX, e.touches[0].clientY);
  }, { passive: true });
  window.addEventListener('mouseleave', function () { ptrOn = 0; }, { passive: true });

  /* Scrolling the deck stirs the field too. */
  var wheel = 0;
  window.addEventListener('wheel', function (e) {
    wheel += Math.max(-1, Math.min(1, e.deltaY / 400));
  }, { passive: true });

  window.addEventListener('resize', resize);
  resize();

  /* ---- loop --------------------------------------------------------- */

  var intensity = parseFloat(getComputedStyle(canvas).getPropertyValue('--bg-intensity')) || 1;
  var last = performance.now(), t0 = last, raf = 0;

  function frame(now) {
    raf = requestAnimationFrame(frame);
    var dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    var time = (now - t0) / 1000;

    ptrVel = [(ptr[0] - ptrPrev[0]) * 12, (ptr[1] - ptrPrev[1]) * 12 - wheel * 0.35];
    ptrPrev = [ptr[0], ptr[1]];
    wheel *= 0.82;

    gl.bindVertexArray(vao);

    gl.useProgram(simProg);
    gl.bindFramebuffer(gl.FRAMEBUFFER, b.fbo);
    gl.viewport(0, 0, simW, simH);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, a.tex);
    gl.uniform1i(uSim.uState, 0);
    gl.uniform2fv(uSim.uAspect, aspect);
    gl.uniform1f(uSim.uTime, time);
    gl.uniform1f(uSim.uDt, dt);
    gl.uniform2fv(uSim.uPointer, ptr);
    gl.uniform2fv(uSim.uPointerVel, ptrVel);
    gl.uniform1f(uSim.uPointerOn, ptrOn);
    gl.drawArrays(gl.TRIANGLES, 0, 3);

    var tmp = a; a = b; b = tmp;

    gl.useProgram(drawProg);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, a.tex);
    gl.uniform1i(uDraw.uState, 0);
    gl.uniform2fv(uDraw.uAspect, aspect);
    gl.uniform1f(uDraw.uTime, time);
    gl.uniform1f(uDraw.uIntensity, intensity);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  function start() { if (!raf) { last = performance.now(); raf = requestAnimationFrame(frame); } }
  function stop() { if (raf) { cancelAnimationFrame(raf); raf = 0; } }

  document.addEventListener('visibilitychange', function () {
    if (document.hidden) stop(); else if (!reduced) start();
  });

  canvas.classList.add('on');

  if (reduced) {
    frame(performance.now());  // one settled frame, then hold still
    stop();
  } else {
    start();
  }
})();
