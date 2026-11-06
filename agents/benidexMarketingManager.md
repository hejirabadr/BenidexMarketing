# Agent benidexMarketingManager – spécification

> Statut : **construit** (instructions dans `agents/benidexMarketingManager/AGENT.md`, scripts dans `agents/benidexMarketingManager/scripts/`). **Bloqué** tant que le quota de génération d'images Google n'est pas activé (erreur 429 sur tous les modèles). Pas de modèle Veo avec la clé actuelle : les vidéos sont des montages animés d'images générées. À lire avec `CLAUDE.md` et `brand/brand-context.md`.

## Rôle
Lire le plan média dans Notion et produire, pour chaque ligne du jour, le contenu (texte + visuels) du produit à couvrir, au format demandé (Reel, Vidéo ou Photo). **Ne publie jamais** : Badr valide et publie.

## Notion (workspace « Benidex Marketing »)
- **Media Plan** : https://app.notion.com/p/b41156e74308469787fc77990de8141c (`collection://2dae0263-bdac-4824-b5a5-8f15c6b6df1e`)
  - Colonnes : Name, Produit, Catégorie, Output (Reel / Vidéo / Photo), Canaux (Instagram / Facebook / LinkedIn / TikTok, un ou plusieurs), Date prévue, Statut (À faire / En cours / Traité / Échec), Explication échec, Notes.
  - **À ajouter à la construction** : colonne « Photos produit » (fichiers ou liens). L'agent utilise **toutes les photos/liens présents dans Notion** (colonne ou corps de la page), sans plafond fixe.
- **Content** : https://app.notion.com/p/97200538e2184433aa727f95e986936d (`collection://b8a3e041-ce0a-4e73-9ba8-a919e8bb29ac`)
  - Formats : Carrousel, Reel, Photo, Vidéo. Statut « À valider » à la création. Folder = chemin des fichiers.
  - **À ajouter à la construction** : colonne « Langue » (Français / Anglais / Arabe).

## Déclenchement
Automatique, chaque jour à **5 h heure de Casablanca** (4 h UTC ; 5 h UTC pendant le ramadan, UTC+0). Nouvelle session sur ce dépôt à chaque exécution, avec accès Notion et clé Gemini.

## Déroulé (modèle : Sonnet 5.5)
1. Lire le Media Plan **dans l'ordre de la liste Notion**.
2. Ne traiter que les lignes **« À faire » dont la Date prévue = aujourd'hui**. Date vide ou autre date : ne rien faire (pas d'échec).
3. **Pas de doublons** : si Content contient déjà le même produit au même format (quel que soit le statut), ne pas refaire.
4. Ligne → « En cours ».
5. Regarder la **photo du produit**, chercher le produit sur internet et sur benidex.com pour comprendre son fonctionnement.
6. Décider seul : angle et public (clients prioritaires du brand-context), hashtags (selon contenu et cible), langue.
7. **Langue** : rotation par canal, Français → Anglais → Arabe → Français… (d'après la colonne Langue du dernier contenu de ce canal dans Content). Jamais de darija.
8. Générer texte (hook, légende, hashtags) et visuels via l'**API Gemini de Google** (Imagen / Veo). Secours possible : gabarits Benidex + ffmpeg.
9. Ranger les fichiers dans le dépôt GitHub : `output/AAAA-MM-JJ/<produit>/` ; commit + push sur la branche de travail ; chemin dans Folder.
10. Créer la ligne dans Content en « À valider » ; ligne du plan → « Traité ».
11. **Problème : statut « Échec » + explication dans « Explication échec »**, sans poser de question.

## Formats par canal (proposition à valider)
| Canal | Reel / Vidéo | Photo |
|---|---|---|
| Instagram | 9:16, 1080×1920 (Reel 15–30 s) | 4:5, 1080×1350 |
| TikTok | 9:16, 1080×1920 | 9:16 |
| Facebook | Reel 9:16 ; Vidéo 16:9 | 4:5 |
| LinkedIn | 16:9, 1920×1080 | 1:1, 1080×1080 |
Vidéo : 20 s maximum. Un fichier par format si plusieurs canaux.

## Checklist « Terminé » (oui/non)
- [ ] Aucun prix affiché
- [ ] « Demandez votre devis » présent
- [ ] Aucune mention de BenQ ni de « au meilleur prix au Maroc »
- [ ] Le produit existe sur benidex.com
- [ ] Logo et couleurs Benidex respectés
- [ ] Reel de 15 à 30 s, vidéo de 20 s maximum
- [ ] Tous les canaux demandés couverts, au bon format
- [ ] Hook, légende et hashtags fournis
- [ ] Contenu en « À valider » dans Content et ligne du plan mise à jour

## Prérequis techniques
- Clé API Google Gemini ajoutée par Badr dans l'environnement « BenidexMarketing » (prise en compte seulement dans une **nouvelle session**).
- Connecteur Notion disponible dans la routine.
- Modèles d'images/vidéos autorisés par la clé : **à tester** dans la nouvelle session.

## Points encore à confirmer
- Tableau des formats par canal.
- Exemple de style : « Table cantine » ou « Coussins de sol colorés » dans Content comme modèle ?
