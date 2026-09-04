# Ligue BN Matchup Generator

Outil de génération de calendrier pour ligues Blood Bowl utilisant Tourplay.

Le projet couvre deux besoins :

1. extraire la liste des coachs depuis une page Tourplay ;
2. générer une saison aléatoire où chaque coach joue au plus une fois contre chaque autre coach.

Il fournit aussi une interface Tkinter pour visualiser les journées et exporter les résultats par journée et par coach.

## Vue d'ensemble

- `export_tourplay.py` extrait les participants depuis une page Tourplay sauvegardée localement ou depuis une URL.
- `matchup_generator.py` charge le fichier des coachs, génère les journées et produit les exports.
- `build.py` et le `Makefile` servent à fabriquer des exécutables avec PyInstaller.

## Prérequis

- Python 3.11 ou plus récent recommandé
- dépendances Python installées depuis `requirements.txt`
- environnement graphique local pour lancer l'interface Tkinter

Installation :

```bash
python -m pip install -r requirements.txt
```

Sous Linux ou macOS, utilisez éventuellement `python3` à la place de `python`.

## Workflow rapide

### 1. Récupérer la page des participants Tourplay

Ouvrez l'onglet `Participants` de votre ligue Tourplay puis enregistrez la page en local.

Vous pouvez utiliser :

- le fichier HTML principal, par exemple `Ligue Blood Bowl - Participants LIGUE BN - SAISON 18.htm`
- ou directement le dossier compagnon `..._files` généré par le navigateur

Le script sait maintenant gérer les deux cas.

### 2. Extraire les coachs

Exemple avec le fichier HTML :

```bash
python export_tourplay.py "Ligue Blood Bowl - Participants LIGUE BN - SAISON 18.htm"
```

Exemple avec le dossier sauvegardé par le navigateur :

```bash
python export_tourplay.py "Ligue Blood Bowl - Participants LIGUE BN - SAISON 18_files"
```

Le script produit :

- `tourplay_data_exported/coachs_extract.csv`
- `tourplay_data_exported/coachs_extract.json`

### 2bis. Generer les posts Discourse par journee

Une fois le calendrier genere (fichier `matchups_enriched.csv`), vous pouvez
produire un post Markdown par journee au format Discourse :

```bash
python generate_discourse_posts.py
```

Le script :

- detecte les dossiers `generated_*` et demande lequel utiliser s'il y en a plusieurs
- demande la saison (ex: `18`) pour generer le tag `saison18` et le titre `[S18]`
- demande la `Periode` de chaque journee (ex: `13/04 au 03/05`)
- applique par defaut les tags : `saisonXX`, `matchup_generator`, `journee`, `calendrier`, `matchs`
- ecrit les fichiers dans `generated_xxx/discourse_posts/`
- publie ensuite les topics via l'API Discourse (par defaut)

Configuration API possible via variables d'environnement :

- `DISCOURSE_URL`
- `DISCOURSE_API_KEY`
- `DISCOURSE_API_USERNAME`
- `DISCOURSE_CATEGORY_ID` (optionnel)

Exemple non interactif pour une seule journee :

```bash
python generate_discourse_posts.py --period "Journee 11=13/04 au 03/05" --no-prompt-periods
```

Exemple non interactif avec saison :

```bash
python generate_discourse_posts.py --season 18 --period "Journee 11=13/04 au 03/05" --no-prompt-periods
```

Selection explicite d'un dossier de generation :

```bash
python generate_discourse_posts.py --season 18 --generated-dir "generated_20260903_204948"
```

Si vous voulez uniquement generer les fichiers markdown sans publier :

```bash
python generate_discourse_posts.py --season 18 --no-post
```

Exemple publication directe via API Discourse :

```bash
python generate_discourse_posts.py \
	--discourse-url "https://forum.ligue-bn.com" \
	--api-key "VOTRE_API_KEY" \
	--api-username "system"
```

### 3. Générer les journées

Lancez l'interface principale :

```bash
python matchup_generator.py
```

Puis :

1. sélectionnez le fichier `coachs_extract.csv`
2. vérifiez le nombre d'équipes détecté
3. choisissez le nombre de journées
4. lancez la génération

## Règles de génération

Le générateur applique les contraintes suivantes :

- le nombre d'équipes doit être pair
- le nombre de journées doit être strictement positif
- le nombre de journées ne peut pas dépasser `n_teams - 1`
- chaque coach joue exactement une fois par journée
- aucune paire de coachs n'est répétée sur la saison générée

La génération n'utilise pas un round-robin figé. Chaque journée est tirée parmi les rencontres encore disponibles, avec retour arrière si une impasse est atteinte.

## Format du fichier des coachs

Le fichier d'entrée utilisé par `matchup_generator.py` doit contenir les colonnes suivantes :

- `num`
- `coach`
- `team`
- `roster`

Le champ `num` sert d'identifiant interne pour le calendrier.

Vous pouvez modifier l'ordre des `num` si vous voulez changer la base de tirage ou préparer un ordre particulier. Évitez de supprimer ou de dupliquer des numéros.

## Résultats générés

Chaque génération crée un dossier du type `generated_YYYYMMDD_HHMMSS/` contenant notamment :

- `matchups_raw.csv` : calendrier brut avec identifiants numériques
- `matchups_enriched.csv` : calendrier enrichi avec noms de coachs, équipes et rosters
- `par_journee/` : exports par journée en Markdown, CSV, PDF et PNG selon les dépendances disponibles
- `par_coach/` : exports par coach en Markdown, CSV et PNG

## Présentation intégrée

L'interface inclut une fenêtre de présentation des journées :

- navigation entre journées
- affichage progressif des rencontres
- lecture automatique
- affichage complet de la journée
- défilement vertical quand une journée contient plus de matchs que l'espace visible

## Limites connues de Tourplay

Tourplay peut masquer certaines informations selon la compétition.

Dans ce cas :

- le nombre réel de participants est récupéré via l'API publique Tourplay si la page sauvegardée est incomplète
- les champs `team` et `roster` peuvent rester partiels ou valoir `Non trouvé`

Exemple courant : une catégorie avec `hideRosters=true` expose le coach et un nom court d'équipe, mais pas le roster complet.

## Build d'exécutables

### Build simple

```bash
python build.py
```

Le script lance le build natif pour la plateforme courante et affiche les commandes à exécuter sur les autres plateformes.

### Avec Makefile

Cibles principales :

- `make build`
- `make linux`
- `make macos`
- `make windows`
- `make build_all`
- `make clean`

Le build Windows via le `Makefile` suppose un environnement `wine` prêt à l'emploi.

## Dépannage

### `ModuleNotFoundError`

Installez les dépendances :

```bash
python -m pip install -r requirements.txt
```

### L'extraction renvoie moins de coachs que prévu

Le script tente automatiquement un fallback via l'API Tourplay quand la page sauvegardée ne contient qu'une partie du virtual scroll.

Si ce n'est pas suffisant :

- vérifiez que vous avez bien sauvegardé la page `Participants`
- vérifiez que le fichier HTML principal et le dossier `..._files` sont côte à côte

### Les exports PDF ou PNG sont désactivés

Installez les dépendances optionnelles de rendu :

- `pandas`
- `reportlab`
- `matplotlib`

## Structure du dépôt

Fichiers principaux :

- `export_tourplay.py`
- `matchup_generator.py`
- `build.py`
- `requirements.txt`
- `Makefile`

## Contribution

Les contributions sont bienvenues, en particulier sur :

- l'amélioration de l'extraction Tourplay
- l'ergonomie de l'interface
- les exports visuels
- la robustesse des builds multi-plateformes
