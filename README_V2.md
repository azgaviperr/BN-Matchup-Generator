# BN Matchup Generator V2

## 🆕 Nouveautés de la Version 2

La Version 2 est une réécriture complète avec une architecture moderne et modulaire:

### Architecture Améliorée
- **Code modulaire** : Séparation claire entre logique métier, interface et exports
- **Meilleure maintenabilité** : Code organisé en modules indépendants
- **Tests intégrés** : Suite de tests pour valider la génération

### Algorithme Amélioré
- **Algorithme round-robin** : Garantit une génération optimale
- **Validation automatique** : Vérifie la cohérence du calendrier
- **Pas de collisions** : Chaque paire d'équipes se rencontre exactement une fois

### Gestion d'Erreurs
- **Validation des entrées** : Vérification complète des paramètres
- **Messages d'erreur clairs** : Diagnostics précis des problèmes
- **Logging intégré** : Traçabilité complète des opérations

### Exports Multiples
- **CSV enrichi** : Avec toutes les informations des coachs
- **JSON** : Format structuré pour intégration avec d'autres outils
- **Markdown** : Pour documentation et partage
- **PDF** : Export professionnel (si reportlab installé)

## 🚀 Installation

```bash
# Installation des dépendances de base
pip install -r requirements.txt

# Pour les exports PDF (optionnel)
pip install reportlab pandas
```

## 📖 Utilisation

### Mode Graphique (GUI)

```bash
python matchup_generator_v2.py
```

L'interface graphique permet de:
- Charger un fichier CSV/JSON de coachs
- Configurer le nombre de journées
- Générer le calendrier
- Visualiser les résultats par journée ou par coach
- Exporter dans différents formats

### Mode Ligne de Commande (CLI)

```bash
# Génération basique
python matchup_generator_v2.py --coaches coachs_extract.csv --days 11

# Avec options avancées
python matchup_generator_v2.py \
    --coaches coachs_extract.csv \
    --days 11 \
    --output mon_calendrier \
    --seed 42 \
    --verbose
```

**Options disponibles:**
- `--coaches` : Fichier CSV ou JSON des coachs (requis)
- `--days` : Nombre de journées à générer (requis)
- `--output` : Répertoire de sortie (auto-généré si omis)
- `--seed` : Graine aléatoire pour reproductibilité
- `--verbose` : Mode verbeux pour debugging

## 📁 Structure des Fichiers

```
src/v2/
├── core/               # Logique métier
│   ├── generator.py    # Générateur de matchups
│   └── models.py       # Modèles de données (Coach, etc.)
├── ui/                 # Interface utilisateur
│   └── main_window.py  # Fenêtre principale
├── exports/            # Exports multiformats
│   └── exporter.py     # Exporteurs CSV/JSON/MD/PDF
└── utils/              # Utilitaires
    └── file_utils.py   # Fonctions fichiers
```

## 📊 Format des Fichiers

### Fichier d'entrée (coachs_extract.csv)

```csv
num,coach,groupe,team,roster
1,Alice,,Eagles,Humans
2,Bob,,Crushers,Orcs
3,Charlie,,Shadows,Dark Elves
4,Diana,,Thunders,Dwarves
```

**Colonnes requises:**
- `num` : Numéro d'équipe (entier unique)
- `coach` : Nom du coach
- `team` : Nom de l'équipe
- `roster` : Race/Roster de l'équipe
- `groupe` : Groupe (optionnel)

### Fichiers de sortie

Le générateur crée un dossier `generated_YYYYMMDD_HHMMSS/` contenant:
- `matchups_enriched.csv` : Planning complet avec détails
- `matchups_raw.csv` : Planning basique (numéros d'équipes)
- `matchups.json` : Format JSON structuré
- `matchups.md` : Documentation Markdown
- `matchups.pdf` : Export PDF (si disponible)
- `par_journee/` : Fichiers par journée

## 🧪 Tests

```bash
# Exécuter les tests
python test_v2.py
```

Les tests valident:
- Génération de calendrier
- Gestion d'erreurs
- Modèles de données
- Workflow complet

## 🔧 Configuration Avancée

### Nombre maximum de journées

Pour N équipes, le nombre maximum de journées est N-1.

**Exemples:**
- 4 équipes → 3 journées max
- 12 équipes → 11 journées max
- 20 équipes → 19 journées max

### Reproductibilité

Utilisez l'option `--seed` pour générer le même calendrier:

```bash
python matchup_generator_v2.py --coaches data.csv --days 11 --seed 42
```

## 🆚 Différences avec V1

| Fonctionnalité | V1 | V2 |
|---------------|----|----|
| Architecture | Monolithique | Modulaire |
| Algorithme | Tentatives aléatoires | Round-robin |
| Validation | Basique | Complète |
| CLI | Non | Oui |
| Tests | Non | Oui |
| Logging | Minimal | Complet |
| Export JSON | Non | Oui |
| API | Non | Préparé pour |

## 🤝 Contribution

La V2 est conçue pour être extensible. Pour contribuer:

1. Forker le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Ajouter des tests pour votre fonctionnalité
4. Faire vos modifications
5. Exécuter les tests (`python test_v2.py`)
6. Soumettre une Pull Request

## 📝 Licence

Même licence que le projet principal (voir LICENSE).

## 🐛 Bugs et Support

Pour signaler un bug ou demander une fonctionnalité, ouvrez une issue sur GitHub.
