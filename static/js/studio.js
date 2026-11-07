document.querySelectorAll('.pause').forEach(button => button.addEventListener('click', () => {
  const paused = button.closest('.ticker').classList.toggle('paused');
  button.setAttribute('aria-pressed', String(paused));
  button.setAttribute('aria-label', paused ? 'Resume animation' : 'Pause animation');
  button.textContent = paused ? '▶' : 'Ⅱ';
}));
const menu = document.querySelector('.menu-toggle');
if (menu) {
  menu.addEventListener('click', () => {
    const opened = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded',String(opened));
    document.querySelector('#navigation').classList.toggle('open',opened);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      menu.setAttribute('aria-expanded','false');
      document.querySelector('#navigation').classList.remove('open');
      document.querySelectorAll('details[open]').forEach(el => el.removeAttribute('open'));
    }
  });
}
