// Injecté via addInitScript : curseur visible, ondes de clic, badge de chapitre.
(() => {
  if (window.__pwOverlayInstalled) return;
  window.__pwOverlayInstalled = true;

  const Z = 2147483647;

  function ensure() {
    if (!document.body) return null;
    let cur = document.getElementById('__pw-cursor');
    if (!cur) {
      cur = document.createElement('div');
      cur.id = '__pw-cursor';
      cur.style.cssText = `position:fixed;left:0;top:0;width:30px;height:34px;z-index:${Z};pointer-events:none;transform:translate(-3px,-2px);filter:drop-shadow(0 2px 4px rgba(0,0,0,0.45));transition:left 0.055s linear, top 0.055s linear;`;
      cur.innerHTML = `<svg width="30" height="34" viewBox="0 0 30 34" xmlns="http://www.w3.org/2000/svg">
        <path d="M 4 2 L 4 26 L 10.2 20.6 L 14 29.5 L 18.6 27.5 L 14.8 18.8 L 23 18.2 Z"
              fill="#ffffff" stroke="#1a1a1a" stroke-width="1.6" stroke-linejoin="round"/>
      </svg>`;
      document.body.appendChild(cur);
      const saved = sessionStorage.getItem('__pw-cursor-pos');
      if (saved) {
        const [x, y] = saved.split(',').map(Number);
        cur.style.left = x + 'px';
        cur.style.top = y + 'px';
      } else {
        cur.style.left = '960px';
        cur.style.top = '700px';
      }
    }
    let mark = document.getElementById('__pw-mark');
    if (!mark) {
      mark = document.createElement('div');
      mark.id = '__pw-mark';
      mark.style.cssText = `position:fixed;right:2px;bottom:2px;width:8px;height:8px;z-index:${Z - 3};pointer-events:none;background:transparent;`;
      document.body.appendChild(mark);
      const c = sessionStorage.getItem('__pw-mark-color');
      if (c) mark.style.background = c;
    }
    let badge = document.getElementById('__pw-badge');
    if (!badge) {
      badge = document.createElement('div');
      badge.id = '__pw-badge';
      badge.style.cssText = `position:fixed;top:18px;right:22px;z-index:${Z - 1};pointer-events:none;display:none;align-items:center;gap:9px;background:rgba(14,15,19,0.82);backdrop-filter:blur(8px);color:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:14.5px;font-weight:600;letter-spacing:0.02em;padding:9px 17px;border-radius:999px;border:1px solid rgba(255,217,0,0.35);box-shadow:0 4px 18px rgba(0,0,0,0.28);`;
      badge.innerHTML = `<span style="width:8px;height:8px;border-radius:50%;background:#FFD900;box-shadow:0 0 8px rgba(255,217,0,0.9);"></span><span id="__pw-badge-text"></span>`;
      document.body.appendChild(badge);
      const savedBadge = sessionStorage.getItem('__pw-badge-text');
      if (savedBadge) {
        badge.style.display = 'flex';
        badge.querySelector('#__pw-badge-text').textContent = savedBadge;
      }
    }
    return cur;
  }

  document.addEventListener('mousemove', (e) => {
    const cur = ensure();
    if (!cur) return;
    cur.style.left = e.clientX + 'px';
    cur.style.top = e.clientY + 'px';
    sessionStorage.setItem('__pw-cursor-pos', e.clientX + ',' + e.clientY);
  }, true);

  document.addEventListener('mousedown', (e) => {
    if (!document.body) return;
    const r = document.createElement('div');
    r.style.cssText = `position:fixed;left:${e.clientX}px;top:${e.clientY}px;width:14px;height:14px;border-radius:50%;z-index:${Z - 2};pointer-events:none;transform:translate(-50%,-50%) scale(0.4);background:rgba(255,217,0,0.32);border:2.5px solid rgba(255,217,0,0.85);transition:transform 0.5s cubic-bezier(0.16,1,0.3,1),opacity 0.5s ease-out;`;
    document.body.appendChild(r);
    requestAnimationFrame(() => {
      r.style.transform = 'translate(-50%,-50%) scale(3.4)';
      r.style.opacity = '0';
    });
    setTimeout(() => r.remove(), 600);
  }, true);

  // Marqueur de beat : pastille 8x8 alternant noir/gris, scannée au montage
  // pour mesurer le temps vidéo réel de chaque réplique.
  window.__beatMark = (i) => {
    ensure();
    const mark = document.getElementById('__pw-mark');
    if (!mark) return;
    const color = i % 2 === 0 ? '#000000' : '#808080';
    mark.style.background = color;
    sessionStorage.setItem('__pw-mark-color', color);
  };

  window.__setBadge = (text) => {
    ensure();
    const badge = document.getElementById('__pw-badge');
    if (!badge) return;
    if (text) {
      badge.style.display = 'flex';
      badge.querySelector('#__pw-badge-text').textContent = text;
      sessionStorage.setItem('__pw-badge-text', text);
    } else {
      badge.style.display = 'none';
      sessionStorage.removeItem('__pw-badge-text');
    }
  };

  const boot = () => ensure();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
