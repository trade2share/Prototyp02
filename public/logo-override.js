// Force-set header/login logo to Spitzner image once the app loads
(function () {
    const logoUrl = '/public/2023-06-06-Spitzner-Logo-RGB.png';
    function setLogo() {
      try {
        const imgs = document.querySelectorAll('img');
        imgs.forEach((img) => {
          const alt = (img.getAttribute('alt') || '').toLowerCase();
          const src = img.getAttribute('src') || '';
          if (
            alt.includes('logo') ||
            src.includes('logo') ||
            img.width <= 64 ||
            img.height <= 64
          ) {
            img.src = logoUrl;
          }
        });
      } catch (e) {
        // noop
      }
    }
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      setTimeout(setLogo, 100);
    } else {
      window.addEventListener('DOMContentLoaded', setLogo);
    }
    // Try again after a short delay to catch late-rendered elements
    setTimeout(setLogo, 600);
  })();


