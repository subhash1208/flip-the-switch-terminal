// Scénario des vidéos - à adapter au projet (renommer en scenario.mjs).
// Chaque entrée de VIDEOS produit UN fichier MP4 : carton d'intro, parcours
// enregistré, carton de fin.
//
// L'API `api` reçue par run() (voir recorder.mjs) :
//   api.beat(idReplique, fn)  - joue une réplique ; fn contient les actions
//   api.cueFrac(0.78)         - attend que la voix atteigne 78 % de la réplique
//                               (= position du mot-clé dans le texte / longueur du texte)
//   api.goto('/chemin')       - navigation (relative à config.baseUrl)
//   api.click(sel) api.hover(sel) api.type(sel, txt, {clear}) api.select(sel, val)
//   api.scrollTo(y) api.scrollIntoView(sel) api.wait(ms) api.setBadge(txt)
//   api.page                  - la Page Playwright pour tout le reste
//
// Règle d'or de la synchro : la voix ANNONCE, l'action SUIT. Caler chaque
// clic via cueFrac sur le moment où le mot est prononcé.
export const VIDEOS = [
  {
    key: 'demo',
    badge: 'Tutoriel · Démo',
    intro: {
      kicker: 'Tutoriel',
      title: 'La <span class="accent">démo</span>',
      subtitle: 'Découverte de l’application',
      holdMs: 3200,
    },
    outro: {
      kicker: 'Mon produit',
      title: 'À vous de <span class="accent">jouer</span>',
      subtitle: 'Tutoriel démo',
      holdMs: 2800,
    },
    async run(api) {
      const { page } = api;
      await api.goto('/login');

      // « Connectez-vous avec votre mot de passe » ~50 %, « cliquez sur Se connecter » ~80 %
      await api.beat('d01', async () => {
        await api.cueFrac(0.5);
        await api.type('#password', 'Demo2026!');
        await api.cueFrac(0.8);
        await api.click('button:has-text("Se connecter")');
        await page.waitForURL('**/dashboard', { waitUntil: 'networkidle' });
      });

      await api.beat('d02', async () => {
        await api.cueFrac(0.4);
        await api.hover('.stat-card', { dur: 320 });
      });
    },
  },
];
