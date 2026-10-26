// Configuration du pipeline vidéo - à adapter au projet (renommer en video.config.mjs).
export default {
  // URL locale de l'application (JAMAIS la prod : environnement local seedé uniquement).
  baseUrl: 'http://127.0.0.1:8000',

  // Commande exécutée avant chaque enregistrement (reset/seed des données de démo).
  // Exécutée via shell, dans `prepareCwd` (défaut : ce dossier).
  prepare: null, // ex: 'php artisan db:seed --class=DemoSeeder --force'
  prepareCwd: null, // ex: '..'

  outDir: 'out',
  viewport: { width: 1920, height: 1080 },
  locale: 'fr-FR',
  timezoneId: 'Europe/Paris',

  // Rythme
  typeDelayMs: 24,    // délai de frappe par caractère
  beatPaddingMs: 300, // marge après chaque réplique
  fade: 0.5,          // durée des fondus enchaînés entre segments (s)

  // Voix off ElevenLabs (gen-voice.mjs). Clé/voix dans .elevenlabs.env :
  //   ELEVENLABS_API_KEY=...
  //   ELEVENLABS_VOICE_ID=...
  voice: {
    enabled: true,
    model: 'eleven_v3', // eleven_v3 | eleven_multilingual_v2
  },

  // Musique de fond. generate:true APPELLE L'API MUSIC ELEVENLABS (consomme des
  // crédits - toujours demander à l'utilisateur avant). Alternative : déposer
  // un fichier voice/music.mp3 et laisser generate:false.
  music: {
    enabled: false,
    generate: false,
    prompt:
      'Understated lo-fi background music for a software tutorial. Soft muted beat, warm electric piano chords, relaxed modern groove, low energy, discreet, no pads, no choirs, no melody hooks, loopable.',
    lengthMs: 150000,
    volume: 0.075,
  },

  // Sous-titres incrustés
  subtitles: {
    enabled: true,
    fontSize: 34,
    maxWidth: 1460,
    marginBottom: 52,
  },
};
