// Génération de la voix off ElevenLabs - UN appel par vidéo (intonation continue),
// découpe par réplique via les timestamps de l'API (synchro exacte au montage).
// Sans clé API : produit un manifest estimé + un script voix-off à générer à la main.
//
// Secrets dans .elevenlabs.env (jamais commités) :
//   ELEVENLABS_API_KEY=sk_...
//   ELEVENLABS_VOICE_ID=...
import { execFileSync } from 'child_process';
import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import config from './video.config.mjs';
import { NARRATION } from './narration.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const VOICE_DIR = path.join(__dirname, 'voice');
fs.mkdirSync(VOICE_DIR, { recursive: true });

let env = {};
const envPath = path.join(__dirname, '.elevenlabs.env');
if (fs.existsSync(envPath)) {
  env = Object.fromEntries(
    fs.readFileSync(envPath, 'utf8')
      .split('\n').filter((l) => l.includes('='))
      .map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim()])
  );
}
const API_KEY = env.ELEVENLABS_API_KEY || process.env.ELEVENLABS_API_KEY;
const VOICE_ID = env.ELEVENLABS_VOICE_ID || process.env.ELEVENLABS_VOICE_ID;
const MODEL = config.voice?.model ?? 'eleven_v3';
const SEP = '\n\n';

const manifestPath = path.join(VOICE_DIR, 'manifest.json');
const manifest = fs.existsSync(manifestPath) ? JSON.parse(fs.readFileSync(manifestPath, 'utf8')) : {};
manifest._meta = manifest._meta || {};

function probeDuration(file) {
  return parseFloat(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file], { encoding: 'utf8' }).trim());
}

/* ---------- Mode sans voix : manifest estimé + script à générer à la main ---------- */
if (!config.voice?.enabled || !API_KEY || !VOICE_ID) {
  console.log('ℹ Voix désactivée ou clé/voix ElevenLabs absente -> mode sous-titres seuls.');
  let txt = 'SCRIPT VOIX-OFF (à générer manuellement, ex. ElevenLabs)\n\n';
  for (const [videoKey, lines] of Object.entries(NARRATION)) {
    txt += `==========  ${videoKey}  ==========\n\n`;
    for (const line of lines) {
      manifest[line.id] = { synthetic: true, duration: Math.max(1.8, (line.text.length * 65 + 500) / 1000), text: line.text };
      txt += line.text + '\n\n';
    }
  }
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  fs.writeFileSync(path.join(VOICE_DIR, 'voix-off-a-generer.txt'), txt);
  console.log('✔ manifest estimé écrit (durées ~65 ms/caractère) + voice/voix-off-a-generer.txt');
  process.exit(0);
}

/* ---------- Voix : un appel one-shot par vidéo, découpe par timestamps ---------- */
for (const [videoKey, lines] of Object.entries(NARRATION)) {
  const fullText = lines.map((l) => l.text).join(SEP);
  const hash = crypto.createHash('md5').update(VOICE_ID + '|' + MODEL + '|oneshot|' + fullText).digest('hex').slice(0, 8);

  if (manifest._meta[videoKey] === hash && lines.every((l) => manifest[l.id] && !manifest[l.id].synthetic && fs.existsSync(path.join(VOICE_DIR, manifest[l.id].file)))) {
    console.log(`= ${videoKey} (cache)`);
    continue;
  }

  console.log(`- Génération one-shot "${videoKey}" (${fullText.length} caractères) -`);
  const body = { text: fullText, model_id: MODEL, voice_settings: { stability: 0.5, similarity_boost: 0.75 } };
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}/with-timestamps?output_format=mp3_44100_128`, {
    method: 'POST',
    headers: { 'xi-api-key': API_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`ElevenLabs ${res.status}: ${(await res.text()).slice(0, 300)}`);
  const json = await res.json();

  const fullFile = path.join(VOICE_DIR, `full-${videoKey}.mp3`);
  fs.writeFileSync(fullFile, Buffer.from(json.audio_base64, 'base64'));
  const fullDur = probeDuration(fullFile);

  const chars = json.alignment.characters;
  const starts = json.alignment.character_start_times_seconds;
  const ends = json.alignment.character_end_times_seconds;
  const returned = chars.join('');

  let cursor = 0;
  const bounds = [];
  for (const line of lines) {
    const idx = returned.indexOf(line.text, cursor);
    if (idx === -1) throw new Error(`réplique introuvable dans l'alignement (${videoKey}/${line.id})`);
    bounds.push({ id: line.id, from: idx, to: idx + line.text.length });
    cursor = idx + line.text.length;
  }

  for (let k = 0; k < bounds.length; k++) {
    const b = bounds[k];
    let f = b.from;
    while (f < b.to && /\s/.test(chars[f])) f++;
    let t = b.to - 1;
    while (t > f && /\s/.test(chars[t])) t--;
    const start = starts[f];
    const end = ends[t];
    const nextStart = k + 1 < bounds.length ? starts[bounds[k + 1].from] : fullDur;

    const cutStart = Math.max(k === 0 ? 0 : ends[bounds[k - 1].to - 1] + 0.02, start - 0.1);
    const cutEnd = Math.min(nextStart - 0.03, end + 0.35, fullDur);

    const clipFile = `clip-${b.id}.wav`;
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-ss', cutStart.toFixed(3), '-to', cutEnd.toFixed(3), '-i', fullFile, '-ar', '44100', '-ac', '1', path.join(VOICE_DIR, clipFile)]);
    manifest[b.id] = { file: clipFile, duration: probeDuration(path.join(VOICE_DIR, clipFile)), text: lines[k].text };
    console.log(`  ✔ ${b.id} ${manifest[b.id].duration.toFixed(2)}s`);
  }
  manifest._meta[videoKey] = hash;
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  console.log(`✔ ${videoKey}: voix continue ${fullDur.toFixed(1)}s découpée en ${lines.length} clips`);
}

/* ---------- Musique de fond (opt-in explicite : consomme des crédits API) ---------- */
const musicFile = path.join(VOICE_DIR, 'music.mp3');
if (config.music?.enabled && config.music?.generate && !fs.existsSync(musicFile)) {
  console.log('- Génération de la musique de fond (API Music ElevenLabs) -');
  const res = await fetch('https://api.elevenlabs.io/v1/music?output_format=mp3_44100_128', {
    method: 'POST',
    headers: { 'xi-api-key': API_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: config.music.prompt, music_length_ms: config.music.lengthMs ?? 150000 }),
  });
  if (!res.ok) throw new Error(`ElevenLabs music ${res.status}: ${(await res.text()).slice(0, 300)}`);
  fs.writeFileSync(musicFile, Buffer.from(await res.arrayBuffer()));
  console.log('✔ musique -> voice/music.mp3');
} else if (config.music?.enabled && !fs.existsSync(musicFile)) {
  console.log('ℹ music.enabled mais voice/music.mp3 absent (generate:false) : déposez un MP3 ou activez generate.');
}

console.log('\n✔ gen-voice terminé');
