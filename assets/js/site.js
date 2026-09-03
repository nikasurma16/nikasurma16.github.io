/* nika sŭr-mã — portfolio */
(function () {
  'use strict';

  /* ---- language ---------------------------------------------------- */

  var KEY = 'nsm-lang';

  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }

  function remember(v) {
    try { localStorage.setItem(KEY, v); } catch (e) { /* private mode */ }
  }

  function apply(lang) {
    document.documentElement.lang = lang;
    var btns = document.querySelectorAll('.lang button');
    for (var i = 0; i < btns.length; i++) {
      btns[i].setAttribute('aria-pressed', String(btns[i].dataset.lang === lang));
    }
  }

  var initial = stored();
  if (!initial) {
    initial = /^ru\b/i.test(navigator.language || '') ? 'ru' : 'en';
  }
  apply(initial);

  document.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('.lang button') : null;
    if (!b) return;
    apply(b.dataset.lang);
    remember(b.dataset.lang);
  });

  /* ---- inline video ------------------------------------------------- */
  /* Some browsers hold even a muted autoplay until the page is touched. */

  var inlineVideos = document.querySelectorAll('.cut video');

  /* Try to play, and only fall back to the poster frame if the browser
     actually refuses — a phone plays these fine until Low Power Mode, and
     iOS answers a refusal by laying its own transport controls over the
     page, which is what has to be avoided. */
  /* The reel has its own play control, so it is never frozen to a still. */
  function isReel(v) { return !!(v.closest && v.closest('.reel')); }

  function freeze(v) {
    if (isReel(v)) return;
    var poster = v.getAttribute('poster');
    if (!poster || !v.parentNode) return;
    var img = document.createElement('img');
    img.src = poster;
    img.alt = '';
    img.decoding = 'async';
    v.parentNode.replaceChild(img, v);
  }

  function nudge() {
    Array.prototype.forEach.call(inlineVideos, function (v) {
      if (!v.isConnected || !v.paused) return;
      var p = v.play();
      if (p && p.catch) p.catch(function () { freeze(v); });
    });
  }

  /* Tap to play where autoplay was refused. A user gesture is allowed even
     in Low Power Mode, which blocks autoplay on iOS outright. */
  var reel = document.querySelector('.reel');
  var reelVideo = reel && reel.querySelector('video');
  if (reelVideo) {
    var markReel = function () {
      reel.classList.toggle('is-paused', reelVideo.paused);
    };
    var toggleReel = function (e) {
      e.preventDefault();
      if (reelVideo.paused) {
        var p = reelVideo.play();
        if (p && p.catch) p.catch(function () { /* still refused */ });
      } else {
        reelVideo.pause();
      }
    };
    reelVideo.addEventListener('click', toggleReel);
    var playBtn = reel.querySelector('.reel-play');
    if (playBtn) playBtn.addEventListener('click', toggleReel);
    ['play', 'pause', 'loadeddata', 'canplay', 'error'].forEach(function (ev) {
      reelVideo.addEventListener(ev, markReel);
    });
    markReel();
    setTimeout(markReel, 1200);
    setTimeout(markReel, 4000);
  }

  if (inlineVideos.length) {
    nudge();
    ['pointerdown', 'keydown', 'wheel', 'touchstart'].forEach(function (ev) {
      window.addEventListener(ev, nudge, { passive: true });
    });
    /* Freeze on an actual refusal, not on a stopwatch: a phone on a slow
       connection needs seconds to buffer, and swapping it out early meant
       a video that could have played never did. The late check only fires
       when nothing has arrived at all. */
    Array.prototype.forEach.call(inlineVideos, function (v) {
      v.addEventListener('error', function () { freeze(v); }, { once: true });
      v.addEventListener('canplay', function () { nudge(); }, { once: true });
      v.addEventListener('loadeddata', function () { nudge(); }, { once: true });
    });
    setTimeout(function () {
      Array.prototype.forEach.call(inlineVideos, function (v) {
        if (v.isConnected && v.paused && v.readyState < 3) freeze(v);
      });
    }, 8000);
  }

  /* ---- paper cutouts ----------------------------------------------- */
  /* Each cutout springs into place the first time it comes into view. */

  /* Measured against the viewport rather than observed: the stylesheet
     hides a cutout until it has landed, so this must not be able to fail
     quietly. A timer lands whatever is left, whatever happened. */

  var waiting = Array.prototype.slice.call(document.querySelectorAll('.cut'));

  function land(el) { el.classList.add('in'); }

  function sweep() {
    var h = window.innerHeight || 800;
    waiting = waiting.filter(function (el) {
      var r = el.getBoundingClientRect();
      if (r.height === 0) return true;
      if (r.top < h * 0.94 && r.bottom > h * 0.06) { land(el); return false; }
      return true;
    });
  }

  /* Throttled on a timer, not on requestAnimationFrame: embedded and
     background views can park the rendering loop indefinitely, and a
     cutout that never lands is a cutout nobody sees. */
  var timer = 0;
  function scheduleSweep() {
    if (timer || !waiting.length) return;
    timer = setTimeout(function () { timer = 0; sweep(); }, 80);
  }

  /* A photograph has no height until it has decoded, so sweep again as
     each one arrives rather than guessing at fixed delays. */
  waiting.forEach(function (el) {
    var img = el.querySelector('img');
    if (img && !img.complete) {
      img.addEventListener('load', scheduleSweep, { once: true });
      img.addEventListener('error', scheduleSweep, { once: true });
    }
    var vid = el.querySelector('video');
    if (vid) {
      vid.addEventListener('loadedmetadata', scheduleSweep, { once: true });
      vid.addEventListener('error', scheduleSweep, { once: true });
    }
  });

  sweep();
  window.addEventListener('scroll', scheduleSweep, { passive: true });
  window.addEventListener('resize', scheduleSweep);
  window.addEventListener('load', sweep);
  document.addEventListener('scroll', scheduleSweep, { passive: true, capture: true });
  setTimeout(sweep, 250);
  setTimeout(sweep, 900);
  setTimeout(function () { waiting.splice(0).forEach(land); }, 3000);

  /* ---- slide deck -------------------------------------------------- */

  var deck = document.querySelector('.deck');
  if (!deck) return;

  var slides = Array.prototype.slice.call(deck.querySelectorAll('.slide'));
  var dots = Array.prototype.slice.call(document.querySelectorAll('.pager button'));
  var current = -1;

  function mark(i) {
    if (i === current) return;
    current = i;
    for (var k = 0; k < dots.length; k++) {
      dots[k].setAttribute('aria-current', String(k === i));
    }
  }

  /* Derive the active slide from the scroll offset rather than from an
     observer: the offset is exact, and it cannot be misread while the
     deck is still being laid out. */
  function sync() {
    var h = deck.clientHeight || 1;
    var i = Math.round(deck.scrollTop / h);
    mark(Math.max(0, Math.min(slides.length - 1, i)));
  }

  var ticking = false;
  deck.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () { ticking = false; sync(); });
  }, { passive: true });
  window.addEventListener('resize', sync);
  sync();

  function goTo(i) {
    if (i < 0 || i >= slides.length) return;
    mark(i);
    deck.scrollTo({ top: i * deck.clientHeight, behavior: 'smooth' });
  }

  dots.forEach(function (b, i) {
    b.addEventListener('click', function () { goTo(i); });
  });

  document.addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'ArrowDown' || e.key === 'PageDown') { e.preventDefault(); goTo(current + 1); }
    else if (e.key === 'ArrowUp' || e.key === 'PageUp') { e.preventDefault(); goTo(current - 1); }
    else if (e.key === 'Home') { e.preventDefault(); goTo(0); }
    else if (e.key === 'End') { e.preventDefault(); goTo(slides.length - 1); }
    else if (e.key === 'Enter') {
      var link = slides[current] && slides[current].querySelector('a.hit');
      if (link) link.click();
    }
  });
})();
