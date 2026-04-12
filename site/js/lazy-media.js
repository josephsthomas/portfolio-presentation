/* ============================================================
   LAZY MEDIA — IntersectionObserver-based image hydration
   Adds 2-slide preload margin for smooth scroll-through
   ============================================================ */

(function () {
  'use strict';

  const images = document.querySelectorAll('img[data-src]');
  if (!images.length) return;

  const supportsIO = 'IntersectionObserver' in window;

  function hydrate(img) {
    const src = img.getAttribute('data-src');
    if (!src) return;
    img.addEventListener('load', () => {
      img.setAttribute('data-loaded', 'true');
      const frame = img.closest('.media-frame');
      if (frame) frame.removeAttribute('data-state');
    }, { once: true });
    img.addEventListener('error', () => {
      const frame = img.closest('.media-frame');
      if (frame) frame.setAttribute('data-state', 'error');
    }, { once: true });
    img.src = src;
    img.removeAttribute('data-src');
  }

  if (!supportsIO) {
    images.forEach(hydrate);
    return;
  }

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          hydrate(entry.target);
          io.unobserve(entry.target);
        }
      });
    },
    {
      // Preload 2 slides ahead in each direction
      rootMargin: '200% 0px',
      threshold: 0.01,
    }
  );

  images.forEach((img) => {
    const frame = img.closest('.media-frame');
    if (frame) frame.setAttribute('data-state', 'loading');
    io.observe(img);
  });
})();
