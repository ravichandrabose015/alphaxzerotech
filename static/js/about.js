const navigationToggle = document.querySelector('.nav-toggle');
const navigationMenu = document.querySelector('.nav-menu');

if (navigationToggle && navigationMenu) {
  navigationToggle.addEventListener('click', () => {
    const isOpen = navigationMenu.classList.toggle('open');
    navigationToggle.setAttribute('aria-expanded', String(isOpen));
    navigationToggle.setAttribute('aria-label', isOpen ? 'Close navigation' : 'Open navigation');
  });

  navigationMenu.addEventListener('click', (event) => {
    if (event.target.closest('a')) {
      navigationMenu.classList.remove('open');
      navigationToggle.setAttribute('aria-expanded', 'false');
      navigationToggle.setAttribute('aria-label', 'Open navigation');
    }
  });
}
