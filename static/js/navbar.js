(() => {
  const header = document.querySelector('[data-site-header]');
  const toggle = document.querySelector('[data-nav-toggle]');
  const navigation = document.querySelector('[data-primary-nav]');
  const dropdown = document.querySelector('[data-nav-dropdown]');
  const dropdownToggle = document.querySelector('[data-dropdown-toggle]');
  if (!header || !toggle || !navigation) return;
  const mobile = window.matchMedia('(max-width: 1120px)');
  let open = false;
  let scrollPosition = 0;
  let savedTop = "";
  const setOpen = (value, restoreFocus = false) => {
    const nextOpen = value && mobile.matches;
    if (nextOpen && !open) {
      scrollPosition = window.scrollY;
      savedTop = document.body.style.top;
      document.body.style.top = `-${scrollPosition}px`;
    }
    const wasOpen = open;
    open = nextOpen;
    toggle.classList.toggle('open', open);
    navigation.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    navigation.inert = mobile.matches && !open;
    document.body.classList.toggle('ax-nav-open', open);
    if (wasOpen && !open) {
      document.body.style.top = savedTop;
      window.scrollTo({ top: scrollPosition, behavior: 'instant' });
    }
    if (restoreFocus) toggle.focus({ preventScroll: true });
  };
  toggle.addEventListener('click', () => setOpen(!open));
  const setDropdown = value => {
    if (!dropdown || !dropdownToggle) return;
    dropdown.classList.toggle('open', value);
    dropdownToggle.setAttribute('aria-expanded', String(value));
  };
  dropdownToggle?.addEventListener('click', event => {
    event.stopPropagation();
    setDropdown(!dropdown.classList.contains('open'));
  });
  navigation.querySelectorAll('a').forEach(link => {
    if (link.classList.contains('active')) link.setAttribute('aria-current', 'page');
    link.addEventListener('click', () => { setDropdown(false); setOpen(false); });
  });
  document.addEventListener('click', event => {
    if (!dropdown?.contains(event.target)) setDropdown(false);
    if (open && !header.contains(event.target)) setOpen(false);
  });
  document.addEventListener('keydown', event => {
    if (!open) return;
    if (event.key === 'Escape') { setOpen(false, true); return; }
    if (event.key !== 'Tab') return;
    const links = [...navigation.querySelectorAll('a[href]')];
    const last = links[links.length - 1];
    if (event.shiftKey && document.activeElement === toggle) {
      event.preventDefault(); last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault(); toggle.focus();
    }
  });
  mobile.addEventListener('change', () => { setDropdown(false); setOpen(false); });
  window.addEventListener('scroll', () => header.classList.toggle('ax-scrolled', window.scrollY > 18), { passive: true });
  setOpen(false);
})();
