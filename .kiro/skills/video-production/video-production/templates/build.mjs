// Montage final - pour chaque vidéo du scénario : fondus xfade entre cartons
// et capture, sous-titres incrustés (PNG rendus par Chromium), voix calée sur
// le temps vidéo RÉEL (pastille marqueur scannée frame par frame), musique
// optionnelle, normalisation loudness. Produit tuto-<key>.mp4 + tuto-<key>.srt.
import { chromium } from 'playwright';
import { execFileSync, spawnSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import config from './video.config.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, config.outDir ?? 'out');
const VOICE_DIR = path.join(__dirname, 'voice');
const SUBS_DIR = path.join(OUT, 'subs');
const FADE = config.fade ?? 0.5;
const W = config.viewport?.width ?? 1920;
const H = config.viewport?.height ?? 1080;

/* ---------- Pré-vol : filtres ffmpeg requis (les builds minimales en omettent) ---------- */
const REQUIRED_FILTERS = ['xfade', 'overlay', 'fade', 'scale', 'fps', 'trim', 'settb', 'setpts', 'format', 'split', 'delogo', 'amix', 'adelay', 'apad', 'atrim', 'aresample', 'loudnorm', 'concat', 'crop'];
{
  const res = spawnSync('ffmpeg', ['-hide_banner', '-filters'], { encoding: 'utf8' });
  const have = new Set(String(res.stdout || '').split('\n').map((l) => l.trim().split(/\s+/)[1]).filter(Boolean));
  const missing = REQUIRED_FILTERS.filter((f) => !have.has(f));
  if (missing.length) {
    console.error(`✖ Filtres ffmpeg manquants : ${missing.join(', ')}\n  Installez une build complète (ex: brew install ffmpeg).`);
    process.exit(1);
  }
}

const timeline = JSON.parse(fs.readFileSync(path.join(OUT, 'timeline.json'), 'utf8'));
const manifestPath = path.join(VOICE_DIR, 'manifest.json');
const manifest = fs.existsSync(manifestPath) ? JSON.parse(fs.readFileSync(manifestPath, 'utf8')) : {};
const hasRealVoice = (id) => manifest[id] && manifest[id].file && !manifest[id].synthetic;

function probeDuration(file) {
  const d = parseFloat(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file], { encoding: 'utf8' }).trim());
  if (!isFinite(d) || d <= 0) throw new Error('durée introuvable: ' + file);
  return d;
}

// Fin du clap de synchro (écran noir ~0,42 s posé par recorder.startSync).
function detectSyncPoint(file) {
  const res = spawnSync('ffmpeg', ['-i', file, '-vf', 'blackdetect=d=0.2:pix_th=0.10', '-an', '-f', 'null', '-'], { encoding: 'utf8' });
  const out = (res.stderr || '') + (res.stdout || '');
  const blacks = [];
  for (const m of out.matchAll(/black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)/g)) {
    blacks.push({ start: parseFloat(m[1]), end: parseFloat(m[2]), dur: parseFloat(m[3]) });
  }
  const clap = blacks.find((b) => b.start < 15 && b.dur >= 0.25 && b.dur <= 1.2);
  if (!clap) throw new Error('clap de synchro introuvable dans ' + file);
  return clap.end;
}

// Temps vidéo RÉEL de chaque beat : scan de la pastille marqueur (8x8 px,
// bas-droit, alternance noir/gris posée par l'overlay), même pipeline
// trim+fps30 que le montage. Corrige la dérive de capture de Playwright
// (frames perdues pendant les navigations).
function extractMarkTimes(file, trimStart, expected) {
  const pre = trimStart ? `trim=start=${trimStart.toFixed(3)},setpts=PTS-STARTPTS,` : '';
  const cropX = W - 9, cropY = H - 9;
  const res = spawnSync('ffmpeg', ['-i', file, '-vf', `${pre}fps=30,crop=6:6:${cropX}:${cropY},scale=1:1,format=gray`, '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], { maxBuffer: 256 * 1024 * 1024 });
  const buf = res.stdout;
  if (!buf || !buf.length) return null;
  const stateOf = (v) => (v < 60 ? 'black' : v <= 175 ? 'gray' : 'absent');
  const expectedColor = (i) => (i % 2 === 0 ? 'black' : 'gray');
  const times = [];
  let cur = 'absent';
  for (let f = 0; f + 1 < buf.length; f++) {
    const st = stateOf(buf[f]);
    if (st !== cur && stateOf(buf[f + 1]) === st) {
      cur = st;
      if (times.length < expected && st === expectedColor(times.length)) times.push(f / 30);
    }
  }
  return times.length === expected ? times : null;
}

function fmtSrt(t) {
  const h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = Math.floor(t % 60), ms = Math.round((t % 1) * 1000);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms).padStart(3, '0')}`;
}

/* ---------- Rendu PNG des sous-titres ---------- */
fs.rmSync(SUBS_DIR, { recursive: true, force: true });
fs.mkdirSync(SUBS_DIR, { recursive: true });
const browser = await chromium.launch();
const subPage = await browser.newPage({ viewport: { width: W, height: 400 }, deviceScaleFactor: 1 });
const sub = config.subtitles ?? {};
await subPage.setContent(`<!DOCTYPE html><html><head><style>
  body { margin:0; background:transparent; display:flex; justify-content:center; align-items:flex-start; }
  #sub {
    display:inline-block; max-width:${sub.maxWidth ?? 1460}px; margin-top:10px;
    background:rgba(11,12,16,0.78); color:#fafafa;
    font:600 ${sub.fontSize ?? 34}px/1.42 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    padding:18px 38px; border-radius:16px; text-align:center; letter-spacing:0.012em;
    border:1px solid rgba(255,255,255,0.09);
    box-shadow:0 6px 24px rgba(0,0,0,0.35); text-shadow:0 1px 2px rgba(0,0,0,0.5);
  }
</style></head><body><div id="sub"></div></body></html>`);

async function renderSubPng(text, file) {
  await subPage.evaluate((t) => { document.getElementById('sub').textContent = t; }, text);
  await subPage.locator('#sub').screenshot({ path: file, omitBackground: true });
}

/* ---------- Construction d'une vidéo ---------- */
async function buildVideo(videoKey) {
  const outName = `tuto-${videoKey}`;
  const segments = timeline.segments.filter((s) => s.video === videoKey);
  if (!segments.length) throw new Error('aucun segment pour ' + videoKey);

  for (const seg of segments) {
    seg.path = path.join(OUT, seg.file);
    seg.trimStart = seg.syncAt != null ? detectSyncPoint(seg.path) : 0;
    seg.duration = probeDuration(seg.path) - seg.trimStart;
  }
  let cum = 0;
  segments.forEach((seg, k) => {
    seg.globalOffset = k === 0 ? 0 : cum - FADE;
    if (k > 0) cum -= FADE;
    cum += seg.duration;
  });
  const total = cum;

  const cues = [];
  segments.forEach((seg) => {
    if (!seg.beats?.length) return;
    const marks = seg.syncAt != null ? extractMarkTimes(seg.path, seg.trimStart, seg.beats.length) : null;
    const base = seg.syncAt ?? 0;
    const beatStart = (i) => (marks ? marks[i] : (seg.beats[i].start - base) / 1000);
    if (marks) console.log(`  marks "${seg.name}": ${seg.beats.length} beats calés sur le temps vidéo mesuré`);
    else if (seg.syncAt != null) console.warn(`  ⚠ marks "${seg.name}": détection incomplète, fallback horloge script`);
    seg.beats.forEach((b, i) => {
      const start = Math.max(seg.globalOffset + beatStart(i), seg.globalOffset + 0.25);
      const next = seg.beats[i + 1];
      const voice = manifest[b.id];
      const dur = voice?.duration ?? Math.max(1.8, b.text.length * 0.065);
      const end = next
        ? seg.globalOffset + beatStart(i + 1) - 0.12
        : Math.min(start + dur + 0.6, seg.globalOffset + seg.duration - FADE);
      cues.push({
        id: b.id, start, end, text: b.text,
        audio: hasRealVoice(b.id) ? path.join(VOICE_DIR, voice.file) : null,
      });
    });
  });

  fs.writeFileSync(
    path.join(OUT, `${outName}.srt`),
    cues.map((c, i) => `${i + 1}\n${fmtSrt(c.start)} --> ${fmtSrt(c.end)}\n${c.text}\n`).join('\n')
  );

  const subsOn = sub.enabled !== false;
  if (subsOn) {
    for (let i = 0; i < cues.length; i++) {
      cues[i].png = path.join(SUBS_DIR, `${videoKey}-${String(i).padStart(3, '0')}.png`);
      await renderSubPng(cues[i].text, cues[i].png);
    }
  }

  const voiced = cues.filter((c) => c.audio);
  const musicPath = path.join(VOICE_DIR, 'music.mp3');
  const hasMusic = config.music?.enabled && fs.existsSync(musicPath);

  const args = ['-y', '-loglevel', 'warning', '-stats'];
  segments.forEach((s) => args.push('-i', s.path));
  if (subsOn) cues.forEach((c) => args.push('-i', c.png));
  voiced.forEach((c) => args.push('-i', c.audio));
  if (hasMusic) args.push('-stream_loop', '-1', '-i', musicPath);

  const NS = segments.length;
  const NP = subsOn ? cues.length : 0;
  let fc = '';
  segments.forEach((s, i) => {
    const pre = s.trimStart ? `trim=start=${s.trimStart.toFixed(3)},setpts=PTS-STARTPTS,` : '';
    fc += `[${i}:v]${pre}fps=30,settb=AVTB,setpts=PTS-STARTPTS,scale=${W}:${H}:flags=bicubic,format=yuv420p[v${i}];`;
  });
  let prev = 'v0';
  for (let k = 1; k < NS; k++) {
    const label = `x${k}`;
    fc += `[${prev}][v${k}]xfade=transition=fade:duration=${FADE}:offset=${segments[k].globalOffset.toFixed(3)}[${label}];`;
    prev = label;
  }
  let cur = prev;
  if (subsOn) {
    cues.forEach((c, i) => {
      const next = `s${i}`;
      fc += `[${cur}][${NS + i}:v]overlay=x=(main_w-overlay_w)/2:y=main_h-overlay_h-${sub.marginBottom ?? 52}:enable='between(t,${c.start.toFixed(2)},${c.end.toFixed(2)})'[${next}];`;
      cur = next;
    });
  }
  // delogo : gomme la pastille marqueur du rendu final
  fc += `[${cur}]delogo=x=${W - 13}:y=${H - 13}:w=12:h=12,format=yuv420p[vout]`;

  const hasAudio = voiced.length > 0 || hasMusic;
  if (voiced.length) {
    fc += ';';
    voiced.forEach((c, i) => {
      fc += `[${NS + NP + i}:a]aresample=44100,adelay=${Math.round(c.start * 1000)}:all=1[a${i}];`;
    });
    fc += voiced.map((_, i) => `[a${i}]`).join('') + `amix=inputs=${voiced.length}:normalize=0[amixed];`;
    fc += `[amixed]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[vn]`;
  }
  if (hasMusic) {
    const mIdx = NS + NP + voiced.length;
    fc += `;[${mIdx}:a]aresample=48000,volume=${config.music.volume ?? 0.075},afade=t=in:st=0:d=1.5,afade=t=out:st=${(total - 2.8).toFixed(2)}:d=2.8[mus]`;
    fc += voiced.length ? `;[vn][mus]amix=inputs=2:normalize=0,apad[aout]` : `;[mus]apad[aout]`;
  } else if (voiced.length) {
    fc += `;[vn]apad[aout]`;
  }

  args.push('-filter_complex', fc, '-map', '[vout]');
  if (hasAudio) args.push('-map', '[aout]', '-c:a', 'aac', '-b:a', '160k');
  args.push('-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-t', total.toFixed(3), '-movflags', '+faststart', path.join(OUT, `${outName}.mp4`));

  console.log(`- Encodage ${outName} (${total.toFixed(1)}s, ${cues.length} répliques${hasMusic ? ', musique' : ''}${voiced.length ? '' : ', SANS voix'}) -`);
  execFileSync('ffmpeg', args, { stdio: 'inherit' });
  console.log(`✔ ${outName}.mp4`);
  return { outName, total };
}

const keys = [...new Set(timeline.segments.map((s) => s.video))];
const results = [];
for (const key of keys) results.push(await buildVideo(key));
await browser.close();

console.log('\n✔ TERMINÉ');
for (const r of results) console.log(`  ${r.outName}.mp4  ${(r.total / 60).toFixed(1)} min`);
