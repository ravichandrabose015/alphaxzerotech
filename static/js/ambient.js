(() => {
  const canvas = document.querySelector('.ambient-network');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let width = 0, height = 0, frame = 0, last = 0;
  const theme = document.body.dataset.view || 'home';
  const seed = [...theme].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  function resize() {
    width = innerWidth; height = innerHeight;
    const dpr = Math.min(devicePixelRatio || 1, 1.5);
    canvas.width = width * dpr; canvas.height = height * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw(0);
  }
  function draw(time) {
    ctx.clearRect(0, 0, width, height);
    const columns = width < 600 ? 13 : 22;
    const rows = 9;
    const hue = 125 + seed % 35;
    const points = [];
    for (let row = 0; row < rows; row++) {
      points[row] = [];
      for (let col = 0; col < columns; col++) {
        const depth = .3 + row / rows;
        const x = width / 2 + (col - columns / 2) * width / columns * depth * 1.8;
        const y = height * .48 + row * height * .062 + Math.sin(col * .48 + row * .36 + time * .00035 + seed) * 25 * depth;
        points[row].push([x, y]);
        ctx.fillStyle = `hsla(${hue},65%,39%,${.1 + depth * .13})`;
        ctx.beginPath(); ctx.arc(x, y, 1.3 * depth, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = `hsla(${hue},45%,45%,.07)`;
        for (const previous of [points[row][col - 1], points[row - 1]?.[col]]) {
          if (previous) { ctx.beginPath(); ctx.moveTo(...previous); ctx.lineTo(x, y); ctx.stroke(); }
        }
      }
    }
  }
  function enabled() { return !reduced.matches && !document.hidden && !document.body.classList.contains('motion-off'); }
  function tick(time) {
    frame = 0;
    if (!enabled()) return;
    if (time - last > 33) { draw(time); last = time; }
    frame = requestAnimationFrame(tick);
  }
  function update() {
    cancelAnimationFrame(frame); frame = 0;
    if (enabled()) frame = requestAnimationFrame(tick);
    else draw(0);
  }
  addEventListener('resize', resize, { passive: true });
  document.addEventListener('visibilitychange', update);
  reduced.addEventListener('change', update);
  resize(); update();
})();
