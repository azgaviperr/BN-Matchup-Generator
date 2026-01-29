# Ligue BN Matchup Generator

Ce projet est une solution complète pour les ligues Blood Bowl qui utilisent Tourplay. Il vous permet d'extraire les participants, de générer un calendrier de matchs équilibré, et même de projeter une présentation animée des rencontres pour vos événements de ligue.

## 🆕 Version 2 Disponible !

**Une réécriture complète avec architecture moderne et améliorée !**

La Version 2 apporte:
- ✅ **Architecture modulaire** - Code mieux organisé et maintenable
- ✅ **Algorithme round-robin** - Génération optimale garantie
- ✅ **Mode CLI** - Utilisation en ligne de commande
- ✅ **Tests intégrés** - Suite de tests automatisés
- ✅ **Exports multiples** - CSV, JSON, Markdown, PDF
- ✅ **Meilleure gestion d'erreurs** - Messages clairs et logging

**→ [Documentation complète V2](README_V2.md)**

**Démarrage rapide V2:**
```bash
# Mode graphique
python matchup_generator_v2.py

# Mode ligne de commande
python matchup_generator_v2.py --coaches coachs_extract.csv --days 11
```

---

## Documentation Version 1 (Legacy)

## 1\. Démarrer

### Étape 1 : Téléchargement des données des participants 📥

Pour que le script fonctionne, vous devez d'abord obtenir les données des coachs depuis votre ligue Tourplay. Malheureusement, le site de Tourplay ne permet pas une extraction directe et automatisée, nous devons donc procéder manuellement le temps de trouver la bonne méthode.

C'est la méthode la plus simple et la plus fiable.

1. **Ouvrez la page des participants :** Naviguez vers l'onglet **Participants** de votre ligue sur Tourplay.
2. **Enregistrez le fichier HTML :**
      * Faites un **clic droit** n'importe où sur la page (en dehors du tableau).
      * Choisissez l'option **"Enregistrer sous..."** (ou "Save as...").
      * Sauvegardez le fichier HTML sur votre ordinateur. Assurez-vous que le nom de fichier se termine bien par `.html` ou `.htm`.
          * **Exemple de nom de fichier :** `Ligue Blood Bowl - Participants LIGUE BN - SAISON 17.html`

Cette méthode garantit que toutes les données nécessaires sont incluses dans le fichier, prêtes à être traitées par le script d'extraction.

-----

### Étape 2 : Extraction des données des coachs

Lancez le script d'extraction en spécifiant le nom de votre fichier HTML :

```bash
python export_tourplay.py "Ligue Blood Bowl - Participants.html"
```

Ce script va créer un fichier **`coachs_extract.csv`** que vous utiliserez pour la suite.

-----

### Étape 3 : Personnalisation (optionnel)

Le fichier `coachs_extract.csv` contient une colonne **`num`**. Si vous voulez un ordre de match complètement aléatoire, vous pouvez modifier ces numéros. Ouvrez le fichier dans un tableur (Excel, LibreOffice, etc.) et attribuez des numéros aléatoires à chaque coach.

> **Conseil :** Laissez les autres colonnes intactes. Le script en a besoin pour identifier correctement les équipes.

-----

## 2\. Génération et présentation des matchs

Une fois votre fichier `coachs_extract.csv` prêt, vous pouvez lancer le script principal :

```bash
python matchup_generator.py
```

Une interface graphique va s'ouvrir, vous offrant plusieurs options :

* **Choix du nombre de journées** : Définissez combien de journées vous souhaitez générer.
* **Génération en un clic** : Le script utilise un algorithme de tournoi à la ronde pour créer un calendrier équilibré.
* **Export des résultats** : Après la génération, un dossier sera créé contenant :
  * Un fichier CSV avec tous les matchs enrichis des informations (coach, équipe, roster).
  * Des fichiers Markdown, CSV et PDF par journée, et des PNG/Markdown par coach pour un partage facile.
* **Visualisation interactive** : L'interface vous permet de parcourir les matchs par journée ou par coach. C'est parfait pour présenter les rencontres de manière claire et visuelle.

-----

## 3\. Fonctionnalités avancées et astuces

* **Simplicité d'utilisation** : L'interface graphique est conçue pour être intuitive. Elle vérifie automatiquement les erreurs de fichiers et vous guide à travers le processus.
* **Personnalisation** : L'ordre des coachs dans le fichier `coachs_extract.csv` détermine l'ordre des matchs. En changeant l'ordre ou les numéros, vous pouvez générer différents calendriers.
* **Historique des générations** : Chaque génération est enregistrée dans un dossier unique, ce qui vous permet de retrouver facilement vos anciens calendriers.

-----

## Contributeurs

Ce projet a été développé et est maintenu par la communauté BN. Vos contributions sont les bienvenues \!
