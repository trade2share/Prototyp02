// Apply custom logos: Schwarzwald left, Spitzner everywhere else
(function () {
  const SPITZNER_LOGO_URL = '/public/spitznerloading.jpeg';
  const SCHWARZWALD_LOGO_URL = '/public/Schwarzwald.png';
  
  function replaceLogo() {
    // Check if we're on the login page
    const loginPage = document.querySelector('.cl-login');
    
    if (loginPage) {
      // Login page: Replace ALL images with Schwarzwald (super aggressive)
      const loginImages = loginPage.querySelectorAll('img');
      loginImages.forEach((img) => {
        // Replace EVERY image in login page with Schwarzwald
        img.src = SCHWARZWALD_LOGO_URL;
        img.srcset = '';
        img.removeAttribute('srcset');
        img.style.cssText = `
          display: block !important;
          max-height: 80px !important;
          max-width: 200px !important;
          width: auto !important;
          height: auto !important;
          object-fit: contain !important;
          opacity: 1 !important;
          visibility: visible !important;
        `;
      });
      
      // Also set background image for login logo containers
      const loginLogoContainers = loginPage.querySelectorAll('.cl-logo, [class*="logo"], a, div');
      loginLogoContainers.forEach((el) => {
        if (el.querySelector('img') || el.tagName === 'A') {
          el.style.backgroundImage = `url(${SCHWARZWALD_LOGO_URL})`;
          el.style.backgroundSize = 'contain';
          el.style.backgroundRepeat = 'no-repeat';
          el.style.backgroundPosition = 'center';
          el.style.minHeight = '60px';
        }
      });
      
      // SUPER aggressive: Replace via innerHTML if needed
      const links = loginPage.querySelectorAll('a');
      links.forEach((link) => {
        const img = link.querySelector('img');
        if (img) {
          img.src = SCHWARZWALD_LOGO_URL;
        }
      });
    }
    
    // Find the header (main app)
    const header = document.querySelector('[data-cy="header"]');
    
    if (header) {
      // Find the leftmost logo/link (typically the app logo on the left)
      const leftLogo = header.querySelector('a:first-child img, a:first-of-type img');
      
      if (leftLogo) {
        // Replace left logo with Schwarzwald
        leftLogo.src = SCHWARZWALD_LOGO_URL;
        leftLogo.srcset = '';
        leftLogo.removeAttribute('srcset');
        leftLogo.style.display = 'block';
        leftLogo.style.maxHeight = '40px';
        leftLogo.style.width = 'auto';
        leftLogo.style.objectFit = 'contain';
      }
      
      // Find all other images in header (right side logos, user avatars, etc.)
      const allHeaderImages = header.querySelectorAll('img');
      allHeaderImages.forEach((img, index) => {
        // Skip the first one (already handled as Schwarzwald)
        if (img !== leftLogo) {
          if (img.src.includes('/logo') || 
              (img.alt && img.alt.toLowerCase().includes('logo'))) {
            
            img.src = SPITZNER_LOGO_URL;
            img.srcset = '';
            img.removeAttribute('srcset');
            img.style.display = 'block';
            img.style.maxHeight = '40px';
            img.style.width = 'auto';
            img.style.objectFit = 'contain';
          }
        }
      });
    }
    
    // Handle all other logos in the page (avatars, etc.) with Spitzner
    const allImages = document.querySelectorAll('img');
    allImages.forEach((img) => {
      // Skip if we're on login page (already handled)
      if (loginPage && img.closest('.cl-login')) {
        return;
      }
      
      // Skip if it's the left header logo
      if (header && header.querySelector('a:first-child img') === img) {
        return;
      }
      
      // Replace other logo images with Spitzner
      if (img.src.includes('/logo') || 
          (img.alt && img.alt.toLowerCase().includes('logo')) ||
          img.closest('.cl-avatar')) {
        
        img.src = SPITZNER_LOGO_URL;
        img.srcset = '';
        img.removeAttribute('srcset');
        img.style.display = 'block';
        img.style.maxHeight = '40px';
        img.style.width = 'auto';
        img.style.objectFit = 'contain';
      }
    });
  }
  
  // Run immediately
  replaceLogo();
  
  // Run after short delays (multiple times to catch dynamic loading)
  setTimeout(replaceLogo, 50);
  setTimeout(replaceLogo, 100);
  setTimeout(replaceLogo, 200);
  setTimeout(replaceLogo, 500);
  setTimeout(replaceLogo, 1000);
  setTimeout(replaceLogo, 2000);
  
  // Keep running every 500ms for the first 10 seconds
  let counter = 0;
  const interval = setInterval(() => {
    replaceLogo();
    counter++;
    if (counter > 20) clearInterval(interval);
  }, 500);
  
  // Watch for DOM changes
  const observer = new MutationObserver(() => {
    replaceLogo();
  });
  
  // Start observing when DOM is ready
  if (document.body) {
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  } else {
    document.addEventListener('DOMContentLoaded', () => {
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    });
  }
})();


