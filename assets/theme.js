(function () {
  const sticky = document.querySelector('[data-sticky-atc]');
  const target = document.getElementById('sticky-atc-target');

  if (sticky && target) {
    const toggleSticky = () => {
      const rect = target.getBoundingClientRect();
      if (rect.bottom < 80) sticky.classList.add('show');
      else sticky.classList.remove('show');
    };

    window.addEventListener('scroll', toggleSticky, { passive: true });
    toggleSticky();
  }

  document.querySelectorAll('[data-scroll-to]').forEach((button) => {
    button.addEventListener('click', () => {
      const id = button.getAttribute('data-scroll-to');
      const element = document.getElementById(id);
      if (element) element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
})();
