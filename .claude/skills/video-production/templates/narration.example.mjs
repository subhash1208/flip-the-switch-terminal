// Répliques voix-off / sous-titres, par vidéo - à adapter au projet
// (renommer en narration.mjs). UNE réplique = UNE idée + UNE action à l'écran.
//
// Règles d'écriture (public débutant) :
// - Nommer les libellés EXACTS des boutons/menus visibles à l'écran.
// - S'adresser à l'audience de la vidéo (« vous », son vocabulaire).
// - Phrases courtes ; la voix est générée d'une traite par vidéo pour
//   une intonation continue, puis découpée et calée réplique par réplique.
export const NARRATION = {
  demo: [
    { id: 'd01', text: "Bienvenue dans ce tutoriel. Connectez-vous avec votre mot de passe, puis cliquez sur Se connecter." },
    { id: 'd02', text: "Voici le tableau de bord : les indicateurs clés sont résumés en haut de page." },
    // ...
  ],
};

export const ALL_LINES = Object.values(NARRATION).flat();
export function lineById(id) {
  const l = ALL_LINES.find((x) => x.id === id);
  if (!l) throw new Error('réplique inconnue: ' + id);
  return l;
}
