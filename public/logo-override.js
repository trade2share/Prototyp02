// Apply different logos for login (PNG-2) vs in-app (spitznerloading.jpeg)
(function () {
  const APP_LOGO_URL = '/public/spitznerloading.jpeg';
  const LOGIN_LOGO_URL = '/public/2023-06-06-Spitzner-Logo-RGB-2.png';

  function setLogo() {
    try {
      const loginRoot = document.querySelector('.cl-login');
      if (loginRoot) {
        // Login: PNG-2
        // Hide dynamic logo endpoint imgs and paint container
        const dynamicLogoImgs = loginRoot.querySelectorAll("img[src*='/logo']");
        dynamicLogoImgs.forEach((img) => (img.style.display = 'none'));

        const loginImgs = loginRoot.querySelectorAll('img');
        loginImgs.forEach((img) => {
          img.src = LOGIN_LOGO_URL;
          img.srcset = '';
          img.removeAttribute('srcset');
        });
        const loginLogoContainers = loginRoot.querySelectorAll('[class*="logo" i], .cl-logo');
        loginLogoContainers.forEach((el) => {
          el.style.backgroundImage = `url(${LOGIN_LOGO_URL})`;
          el.style.backgroundSize = 'contain';
          el.style.backgroundRepeat = 'no-repeat';
          el.style.backgroundPosition = 'left center';
        });
      }

      // App header (non-login): JPEG
      const header = document.querySelector("[data-cy='header']");
      if (header) {
        const headerImgs = header.querySelectorAll('img');
        headerImgs.forEach((img) => {
          img.src = APP_LOGO_URL;
          img.srcset = '';
          img.removeAttribute('srcset');
        });
        const logoContainers = header.querySelectorAll('.cl-logo, [class*="logo" i]');
        logoContainers.forEach((el) => {
          el.style.backgroundImage = `url(${APP_LOGO_URL})`;
          el.style.backgroundSize = 'contain';
          el.style.backgroundRepeat = 'no-repeat';
          el.style.backgroundPosition = 'left center';
        });
      }
    } catch (e) {}
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(setLogo, 100);
  } else {
    window.addEventListener('DOMContentLoaded', setLogo);
  }
  setTimeout(setLogo, 600);
})();


