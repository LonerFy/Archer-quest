# Archer Quest

Roguelite d'archer salle par salle, écrit en **Python (pygame-ce)** et compilé en **WebAssembly avec pygbag** pour tourner dans le navigateur via GitHub Pages.

**Jouer :** https://lonerfy.github.io/archer-quest/ *(après le premier déploiement)*

## Principe

- Déplacez-vous au clavier (ZQSD, WASD, flèches) ou en maintenant puis glissant (souris, tactile).
- Immobile, l'archer tire automatiquement sur l'ennemi le plus proche.
- Nettoyez la salle, passez la sortie, choisissez une amélioration. Boss toutes les 5 salles, nouveau biome après chaque boss.
- `P` / `Échap` : pause · `M` : son · `1 2 3` : choisir une carte · `R` : relancer

## Nouveautés par rapport à la version HTML

- **Contrôles clavier** (AZERTY et QWERTY) en plus du joystick virtuel, qui est maintenant affiché.
- **Nouvel ennemi, le chargeur** (dès la salle 3) : il annonce sa charge par une ligne rouge avant de foncer.
- **Boss à deux phases** : sous 50 % de PV, il accélère, tire en éventail de 5 et lâche des anneaux de projectiles.
- **Apparition des ennemis** : 0,6 s pendant laquelle ils sont inoffensifs, pour éviter les dégâts injustes en entrant dans une salle.
- **Ennemis qui ne s'empilent plus** (séparation physique).
- **L'or sert enfin** : il permet de relancer les améliorations (coût croissant).
- **Nouvelles améliorations** : Tir arrière, Vampirisme. Chaque amélioration a un plafond et n'est plus proposée une fois au maximum (l'ancien Multi-tir pouvait sortir alors qu'il était bloqué à 5).
- **Record sauvegardé** (localStorage) et statistiques de fin de partie (ennemis vaincus, temps).
- **Pause** manuelle et automatique quand l'onglet perd le focus. Son coupable et mémorisé.
- L'or restant est aspiré automatiquement une fois la salle nettoyée.

## Lancer en local

```bash
pip install -r requirements.txt
python game/main.py          # version ordinateur
python -m pygbag game        # version web sur http://localhost:8000
pytest                       # tests de la logique
```

## Publier sur GitHub Pages

1. Créer le dépôt `archer-quest` sur GitHub et pousser la branche `main`.
2. Dans **Settings → Pages**, choisir **Source : GitHub Actions**.
3. À chaque push, le workflow `.github/workflows/deploy.yml` lance les tests, compile le jeu avec pygbag et le publie.

Le premier chargement dans le navigateur prend quelques secondes, le temps de télécharger l'interpréteur Python en WebAssembly. pygbag affiche ensuite un écran « cliquez pour démarrer », nécessaire pour autoriser le son.

## Architecture

```
game/
  main.py              point d'entrée (boucle asyncio requise par pygbag)
  archer/
    config.py          constantes, biomes
    entities.py        joueur, ennemis, projectiles (données pures)
    upgrades.py        améliorations, tirage pondéré
    world.py           simulation complète, sans pygame -> testable
    app.py             états, entrées, boucle
    render.py          rendu, HUD, écrans, icônes vectorielles
    layout.py          positions des éléments d'interface
    audio.py           sons synthétisés (aucun fichier audio)
    storage.py         sauvegarde navigateur / ordinateur
tests/test_world.py    tests unitaires de la logique
```

La logique (`world.py`) est séparée du rendu : elle ne dépend pas de pygame, s'exécute avec une graine aléatoire fixe et se teste en CI sans écran.

## Licence

MIT - AMOUSSOU-GUENOU Donald
