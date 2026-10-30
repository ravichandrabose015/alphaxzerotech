(() => {
  const header = document.querySelector('[data-site-header]');
  const toggle = document.querySelector('[data-nav-toggle]');
  const navigation = document.querySelector('[data-primary-nav]');

  if (!header || !toggle || !navigation) return;

  const closeNavigation = () => {
    toggle.classList.remove('open');
    navigation.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('ax-nav-open');
  };

  toggle.addEventListener('click', () => {
    const isOpen = navigation.classList.toggle('open');
    toggle.classList.toggle('open', isOpen);
    toggle.setAttribute('aria-expanded', String(isOpen));
    document.body.classList.toggle('ax-nav-open', isOpen);
  });

  navigation.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeNavigation));
  window.addEventListener('resize', () => { if (window.innerWidth > 1120) closeNavigation(); });
  window.addEventListener('scroll', () => header.classList.toggle('ax-scrolled', window.scrollY > 18), { passive: true });
})();
