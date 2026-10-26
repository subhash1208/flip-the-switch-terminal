// Resserre les clips voix SANS régénération API : coupe les silences de
// tête/queue et compresse les pauses internes longues (les voix TTS type
// eleven_v3 contiennent souvent 0,8-1,4 s de pause entre groupes de mots).
// Idempotent : repart toujours de voice/manifest-original.json.
import { execFileSync, spawnSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const VOICE_DIR = path.join(__dirname, 'voice');
const manifestPath = path.join(VOICE_DIR, 'manifest.json');
const backupPath = path.join(VOICE_DIR, 'manifest-original.json');

if (!fs.existsSync(manifestPath)) {
  console.log('ℹ pas de manifest voix - lancez gen-voice.mjs d\'abord.');
  process.exit(0);
}
if (!fs.existsSync(backupPath)) fs.copyFileSync(manifestPath, backupPath);
const manifest = JSON.parse(fs.readFileSync(backupPath, 'utf8'));

const NOISE = '-40dB';
const MIN_SIL = 0.3;    // durée minimale d'un silence détectable (s)
const KEEP_INNER = 0.3; // pause interne conservée (s)
const HEAD_KEEP = 0.12;
const TAIL_KEEP = 0.18;

function probeDuration(file) {
  return parseFloat(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file], { encoding: 'utf8' }).trim());
}

// ffmpeg loggue silencedetect sur STDERR -> spawnSync, pas execFileSync.
function detectSilences(file) {
  const res = spawnSync('ffmpeg', ['-i', file, '-af', `silencedetect=noise=${NOISE}:d=${MIN_SIL}`, '-f', 'null', '-'], { encoding: 'utf8' });
  const out = (res.stderr || '') + (res.stdout || '');
  const silences = [];
  let cur = null;
  for (const line of String(out).split('\n')) {
    const ms = line.match(/silence_start: ([\d.]+)/);
    const me = line.match(/silence_end: ([\d.]+)/);
    if (ms) cur = { start: parseFloat(ms[1]) };
    if (me && cur) { cur.end = parseFloat(me[1]); silences.push(cur); cur = null; }
  }
  return silences;
}

let totalBefore = 0, totalAfter = 0;

for (const [id, m] of Object.entries(manifest)) {
  if (id.startsWith('_') || !m.file || m.synthetic) continue;
  const src = path.join(VOICE_DIR, m.file);
  const dur = probeDuration(src);
  const silences = detectSilences(src);

  const cuts = [];
  for (const s of silences) {
    const atHead = s.start <= 0.05;
    const atTail = s.end >= dur - 0.05;
    if (atHead) {
      if (s.end - HEAD_KEEP > 0.02) cuts.push([0, s.end - HEAD_KEEP]);
    } else if (atTail) {
      if (dur - (s.start + TAIL_KEEP) > 0.02) cuts.push([s.start + TAIL_KEEP, dur]);
    } else if (s.end - s.start > KEEP_INNER + 0.12) {
      const half = KEEP_INNER / 2;
      cuts.push([s.start + half, s.end - half]);
    }
  }

  if (!cuts.length) {
    manifest[id] = { ...m, cuts: [] };
    totalBefore += dur; totalAfter += dur;
    continue;
  }

  const keeps = [];
  let pos = 0;
  for (const [cs, ce] of cuts) {
    if (cs - pos > 0.01) keeps.push([pos, cs]);
    pos = ce;
  }
  if (dur - pos > 0.01) keeps.push([pos, dur]);

  let fc = '';
  keeps.forEach(([a, b], i) => {
    fc += `[0:a]atrim=${a.toFixed(4)}:${b.toFixed(4)},asetpts=PTS-STARTPTS[p${i}];`;
  });
  fc += keeps.map((_, i) => `[p${i}]`).join('') + `concat=n=${keeps.length}:v=0:a=1[out]`;

  const trimFile = m.file.replace(/\.wav$/, '-trim.wav');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', src, '-filter_complex', fc, '-map', '[out]', path.join(VOICE_DIR, trimFile)]);

  const newDur = probeDuration(path.join(VOICE_DIR, trimFile));
  manifest[id] = {
    ...m,
    file: trimFile,
    duration: newDur,
    cuts: cuts.map(([a, b]) => [Math.round(a * 1000), Math.round(b * 1000)]),
  };
  totalBefore += dur; totalAfter += newDur;
  console.log(`✔ ${id}  ${dur.toFixed(2)}s -> ${newDur.toFixed(2)}s  (${cuts.length} coupe(s))`);
}

fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
if (totalBefore > 0) {
  console.log(`\n✔ Voix totale : ${totalBefore.toFixed(0)}s -> ${totalAfter.toFixed(0)}s (-${(100 * (1 - totalAfter / totalBefore)).toFixed(0)}%)`);
}
