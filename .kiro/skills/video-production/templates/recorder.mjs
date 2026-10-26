// Enregistreur générique de vidéos tutorielles (Playwright).
// Ne PAS modifier ce fichier pour un projet : le scénario vit dans scenario.mjs,
// les répliques dans narration.mjs, la config dans video.config.mjs.
//
//   FAST=1 node recorder.mjs   -> répétition rapide (valide les sélecteurs, ~1 min)
//   node recorder.mjs          -> enregistrement réel (calé sur les durées de voix)
import { chromium } from 'playwright';
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import config from './video.config.mjs';
import { VIDEOS } from './scenario.mjs';
import { lineById } from './narration.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, config.outDir ?? 'out');
const FAST = !!process.env.FAST;
const TYPE_DELAY = FAST ? 3 : (config.typeDelayMs ?? 24);
const VIEW = config.viewport ?? { width: 1920, height: 1080 };

let manifest = {};
const manifestPath = path.join(__dirname, 'voice', 'manifest.json');
if (fs.existsSync(manifestPath)) {
  manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
}
function voiceDur(id) {
  const m = manifest[id];
  if (m && isFinite(m.duration)) return m.duration * 1000;
  // Pas de voix générée : estimation lecture FR ~65 ms/caractère.
  return Math.max(1800, lineById(id).text.length * 65 + 500);
}

fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

if (config.prepare) {
  console.log('- prepare:', config.prepare);
  execSync(config.prepare, { cwd: config.prepareCwd ?? __dirname, stdio: 'inherit' });
}

const timeline = { recordedAt: new Date().toISOString(), fast: FAST, segments: [] };
const browser = await chromium.launch({ headless: true });

function ease(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

async function recordSegment(name, { video, overlay = true, badge = null }, run) {
  const context = await browser.newContext({
    viewport: VIEW,
    deviceScaleFactor: 1,
    locale: config.locale ?? 'fr-FR',
    timezoneId: config.timezoneId ?? 'Europe/Paris',
    recordVideo: { dir: OUT, size: VIEW },
  });
  if (overlay) await context.addInitScript({ path: path.join(__dirname, 'lib', 'overlay.js') });
  const page = await context.newPage();
  page.on('dialog', (d) => d.accept().catch(() => {}));
  page.setDefaultTimeout(25000);

  const seg = { name, video, beats: [] };
  const t0 = Date.now();
  const now = () => Date.now() - t0;
  let last = { x: VIEW.width / 2, y: VIEW.height * 0.65 };
  let beatStart = 0;
  let beatLineId = null;
  let beatIndex = 0;
  const S = (ms) => (FAST ? Math.min(ms, 80) : ms);

  const api = {
    page,
    config,
    async wait(ms) {
      await page.waitForTimeout(S(ms));
    },
    // Attend que la voix du beat courant atteigne `frac` (0..1) de sa durée.
    // Pour caler une action sur un mot : frac = position du mot dans le texte
    // (index de caractère / longueur du texte). Robuste après trim des silences.
    async cueFrac(frac) {
      if (FAST) return;
      const target = Math.min(frac, 0.97) * voiceDur(beatLineId);
      const elapsed = now() - beatStart;
      if (elapsed < target) await page.waitForTimeout(target - elapsed);
    },
    async beat(lineId, fn) {
      const { text } = lineById(lineId);
      if (seg.syncAt == null) await api.startSync();
      beatStart = now();
      beatLineId = lineId;
      await page.evaluate((i) => window.__beatMark && window.__beatMark(i), beatIndex).catch(() => {});
      beatIndex++;
      if (fn) await fn();
      const minDur = FAST ? 200 : Math.max(1100, voiceDur(lineId) + (config.beatPaddingMs ?? 300));
      const elapsed = now() - beatStart;
      if (elapsed < minDur) await page.waitForTimeout(minDur - elapsed);
      seg.beats.push({ id: lineId, start: beatStart, end: now(), text });
      console.log(`  [${name}] ${(now() / 1000).toFixed(1)}s  ${lineId}  ${text.slice(0, 52)}`);
    },
    async glide(x, y, durMs) {
      const dist = Math.hypot(x - last.x, y - last.y);
      if (dist < 2) return;
      const dur = S(durMs ?? Math.min(680, Math.max(200, dist * 0.62)));
      const steps = Math.max(10, Math.round(dur / 12));
      for (let i = 1; i <= steps; i++) {
        const t = ease(i / steps);
        await page.mouse.move(last.x + (x - last.x) * t, last.y + (y - last.y) * t);
        await page.waitForTimeout(Math.max(4, dur / steps - 4));
      }
      last = { x, y };
    },
    loc(sel) {
      return typeof sel === 'string' ? page.locator(sel).first() : sel;
    },
    async hover(sel, opts = {}) {
      const el = api.loc(sel);
      await el.waitFor({ state: 'visible' });
      await api.scrollIntoView(el);
      const box = await el.boundingBox();
      if (!box) throw new Error('boundingBox introuvable: ' + sel);
      const x = box.x + box.width * (opts.ax ?? 0.5);
      const y = box.y + box.height * (opts.ay ?? 0.5);
      await api.glide(x, y, opts.dur);
      return { x, y };
    },
    async click(sel, opts = {}) {
      await api.hover(sel, opts);
      await page.waitForTimeout(S(110));
      await page.mouse.down();
      await page.waitForTimeout(S(60));
      await page.mouse.up();
    },
    async type(sel, text, { clear = false } = {}) {
      await api.click(sel);
      if (clear) {
        await page.keyboard.press('ControlOrMeta+a');
        await page.keyboard.press('Backspace');
        await page.waitForTimeout(S(100));
      }
      await page.keyboard.type(text, { delay: TYPE_DELAY });
    },
    // <select> natif : pas de vrai clic (le menu OS n'est pas capturé en vidéo).
    async select(sel, value) {
      await api.hover(sel);
      await api.loc(sel).selectOption(value);
      await page.waitForTimeout(S(180));
    },
    async scrollIntoView(el) {
      const target = api.loc(el);
      const y = await target.evaluate((node) => {
        const r = node.getBoundingClientRect();
        const vh = window.innerHeight;
        if (r.top >= 90 && r.bottom <= vh - 90) return -1;
        return Math.max(0, window.scrollY + r.top - vh / 2 + r.height / 2);
      });
      if (y >= 0) await api.scrollTo(y);
    },
    async scrollTo(y) {
      await page.evaluate(
        async ({ ty, fast }) => {
          const sy = window.scrollY;
          const dist = ty - sy;
          if (Math.abs(dist) < 4) return;
          const dur = fast ? 50 : Math.min(750, Math.max(280, Math.abs(dist) * 0.5));
          const start = performance.now();
          await new Promise((res) => {
            function frame(t) {
              let p = Math.min(1, (t - start) / dur);
              p = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
              window.scrollTo(0, sy + dist * p);
              if (p < 1) requestAnimationFrame(frame);
              else res();
            }
            requestAnimationFrame(frame);
          });
        },
        { ty: y, fast: FAST }
      );
      await page.waitForTimeout(S(120));
    },
    async setBadge(text) {
      await page.evaluate((t) => window.__setBadge && window.__setBadge(t), text).catch(() => {});
    },
    async goto(url) {
      const full = /^https?:/.test(url) ? url : (config.baseUrl ?? '') + url;
      await page.goto(full, { waitUntil: 'networkidle' });
      if (badge) await api.setBadge(badge);
    },
    // Clap de synchro : écran noir bref, détecté au montage (blackdetect) pour
    // recaler l'horloge du script sur le temps réel de la vidéo. Appelé
    // automatiquement au premier beat si oublié.
    async startSync() {
      if (seg.syncAt != null) return;
      await page.evaluate(() => {
        const d = document.createElement('div');
        d.id = '__sync';
        d.style.cssText = 'position:fixed;inset:0;background:#000;z-index:2147483647';
        document.body.appendChild(d);
      });
      await page.waitForTimeout(420);
      seg.syncAt = now();
      await page.evaluate(() => document.getElementById('__sync')?.remove());
      await page.waitForTimeout(80);
    },
  };

  await run(api);
  await page.waitForTimeout(S(600));

  const video_ = page.video();
  await context.close();
  const vpath = await video_.path();
  const target = path.join(OUT, `${name}.webm`);
  fs.renameSync(vpath, target);
  seg.file = path.basename(target);
  timeline.segments.push(seg);
  console.log(`✔ segment "${name}" enregistré`);
}

async function recordCard(name, video, { kicker = '', title = '', subtitle = '', holdMs = 3200 }) {
  await recordSegment(name, { video, overlay: false }, async (api) => {
    const params = new URLSearchParams({ kicker, title, subtitle });
    await api.page.goto('file://' + path.join(__dirname, 'cards', 'card.html') + '?' + params.toString());
    await api.page.waitForTimeout(FAST ? 300 : holdMs);
  });
}

for (const video of VIDEOS) {
  if (video.intro) await recordCard(`${video.key}-00-intro`, video.key, video.intro);
  await recordSegment(`${video.key}-10-main`, { video: video.key, badge: video.badge ?? null }, video.run);
  if (video.outro) await recordCard(`${video.key}-20-outro`, video.key, video.outro);
}

await browser.close();
fs.writeFileSync(path.join(OUT, 'timeline.json'), JSON.stringify(timeline, null, 2));
console.log('\n✔ Tous les segments sont enregistrés. Timeline : ' + path.join(config.outDir ?? 'out', 'timeline.json'));
