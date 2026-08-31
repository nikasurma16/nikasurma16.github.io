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
