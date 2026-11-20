/* =====================================================================
   HOME PAGE SCRIPT (home.js)
   1. Makes the navbar solid white once you scroll down.
   2. Pause/play button for the background video.
   3. Pauses the video for visitors who prefer reduced motion.
   ===================================================================== */

// Wait until the HTML has loaded before looking for elements.
document.addEventListener('DOMContentLoaded', () => {

  /* -------- 1. Navbar: transparent at the top, solid after scrolling -------- */
  const navbar = document.querySelector('.page-home .navbar');

  const updateNavbar = () => {
    // classList.toggle(name, condition) adds the class if the condition is true
    // and removes it if false. "is-scrolled" is styled in home.css.
    if (navbar) navbar.classList.toggle('is-scrolled', window.scrollY > 40);
  };
  updateNavbar();                                            // run once on load
  window.addEventListener('scroll', updateNavbar, { passive: true }); // and on every scroll


  /* -------- 2. Video pause / play button -------- */
  const video = document.querySelector('.vh-video');
  const toggle = document.querySelector('[data-video-toggle]');
  if (!video || !toggle) return;   // stop here if the elements aren't on the page

  // Update the button's icon and screen-reader label to match the video's state.
  const syncButton = () => {
    const paused = video.paused;
    toggle.innerHTML = paused ? '<i class="bi bi-play-fill"></i>' : '<i class="bi bi-pause-fill"></i>';
    toggle.setAttribute('aria-label', paused ? 'Play background video' : 'Pause background video');
  };

  toggle.addEventListener('click', () => {
    if (video.paused) {
      video.play();
    } else {
      video.pause();
    }
  });
  // These events fire whenever the video starts or stops, so the button always matches.
  video.addEventListener('play', syncButton);
  video.addEventListener('pause', syncButton);


  /* -------- 3. Respect "reduce motion" -------- */
  // matchMedia checks the visitor's operating system setting.
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    video.removeAttribute('autoplay');
    video.pause();   // the poster image stays visible instead
  }
  syncButton();
});
