/* ============================================================
   DECK — keyboard nav, slide counter, progress, deep-link
   ============================================================ */

(function () {
  'use strict';

  const slides = Array.from(document.querySelectorAll('.slide'));
  if (!slides.length) return;

  const total = slides.length;

  // --- Slide counter element ---
  const counter = document.querySelector('.deck-counter');
  const progress = document.querySelector('.deck-progress__bar');

  // --- Keyboard nav ---
  function currentIndex() {
    const y = window.scrollY + window.innerHeight / 2;
    for (let i = 0; i < slides.length; i++) {
      const r = slides[i].getBoundingClientRect();
      const top = r.top + window.scrollY;
      if (top <= y && top + r.height > y) return i;
    }
    return 0;
  }

  function go(index) {
    index = Math.max(0, Math.min(total - 1, index));
    slides[index].scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  document.addEventListener('keydown', (e) => {
    // Ignore if in an input / editable element
    if (e.target.matches('input, textarea, [contenteditable]')) return;

    switch (e.key) {
      case 'ArrowDown':
      case 'ArrowRight':
      case 'PageDown':
      case ' ':
      case 'j':
        e.preventDefault();
        go(currentIndex() + 1);
        break;
      case 'ArrowUp':
      case 'ArrowLeft':
      case 'PageUp':
      case 'k':
        e.preventDefault();
        go(currentIndex() - 1);
        break;
      case 'Home':
        e.preventDefault();
        go(0);
        break;
      case 'End':
        e.preventDefault();
        go(total - 1);
        break;
    }
  });

  // --- Update counter + progress + deep-link ---
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && entry.intersectionRatio > 0.5) {
          const idx = slides.indexOf(entry.target);
          if (idx === -1) return;
          const n = idx + 1;
          if (counter) counter.textContent = String(n).padStart(2, '0') + ' / ' + String(total).padStart(2, '0');
          if (progress) progress.style.width = (n / total * 100) + '%';
          if (history.replaceState) history.replaceState(null, '', '#slide-' + n);
        }
      });
    },
    { threshold: [0.5] }
  );

  slides.forEach((slide) => observer.observe(slide));

  // --- Deep-link support on load ---
  if (location.hash && location.hash.startsWith('#slide-')) {
    const n = parseInt(location.hash.slice(7), 10);
    if (n >= 1 && n <= total) {
      // Wait a tick for layout
      requestAnimationFrame(() => go(n - 1));
    }
  }
})();
