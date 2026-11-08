# Agent benidexMarketingManager – spécification

> Statut : **construit** (instructions dans `agents/benidexMarketingManager/AGENT.md`, scripts dans `agents/benidexMarketingManager/scripts/`). **Option A retenue** : pas d'IA d'images (quota Google bloqué) ; l'agent compose posts et reels à partir de vraies photos (scripts `compose_media.py`, `fetch_product_photos.py`). Si la page produit ne marche pas, l'agent cherche données et photos sur internet. À lire avec `CLAUDE.md` et `brand/brand-context.md`.

## Rôle
Lire le plan média dans Notion et produire, pour chaque ligne du jour, le contenu (texte + visuels) du produit à couvrir, au format demandé (Reel, Vidéo ou Photo). **Publie systématiquement** les contenus contrôlés sur les comptes connectés via Windsor (aujourd'hui : Instagram @benidex.maroc pour les vidéos et photos). **S'il n'a rien à publier ou si le compte n'est pas connecté, il ne publie rien.** Voir `AGENT.md` §8.

## Notion (workspace « Benidex Marketing »)
- **Media Plan** : https://app.notion.com/p/b41156e74308469787fc77990de8141c (`collection://2dae0263-bdac-4824-b5a5-8f15c6b6df1e`)
  - Colonnes : Name, Produit, Catégorie, Output (Reel / Vidéo / Photo), Canal (Instagram / Facebook / LinkedIn / TikTok, **un seul par ligne**), Date prévue, Statut (À faire / En cours / Traité / Échec), Explication échec, Notes.
  - **À ajouter à la construction** : colonne « Photos produit » (fichiers ou liens). L'agent utilise **toutes les photos/liens présents dans Notion** (colonne ou corps de la page), sans plafond fixe.
- **Content** : https://app.notion.com/p/97200538e2184433aa727f95e986936d (`collection://b8a3e041-ce0a-4e73-9ba8-a919e8bb29ac`)
  - Formats : Carrousel, Reel, Photo, Vidéo. Statut « À valider » à la création. Folder = chemin des fichiers.
  - **À ajouter à la construction** : colonne « Langue » (Français / Anglais / Arabe).

## Déclenchement
Automatique, chaque jour à **18 h GMT** (19 h à Casablanca ; 18 h pendant le ramadan). Nouvelle session sur ce dépôt à chaque exécution, avec accès Notion et clé Gemini.

## Déroulé (modèle : Sonnet 5.5)
1. Lire le Media Plan **dans l'ordre de la liste Notion**.
2. Ne traiter que les lignes **« À faire »** avec une **Date prévue renseignée, aujourd'hui ou passée** (les lignes en retard sont exécutées). **Date vide ou future : ne rien faire** (pas d'échec).
3. **Pas de doublons** : si Content contient déjà le même produit au même format (quel que soit le statut), ne pas refaire.
4. Ligne → « En cours ».
5. **Photos** : colonne « Photos produit » d'abord ; **si elle est vide, prendre les photos sur la page du produit** (lien dans la colonne Produit). Regarder la photo, chercher le produit sur internet et sur benidex.com pour comprendre son fonctionnement.
6. Décider seul : angle et public (clients prioritaires du brand-context), hashtags (selon contenu et cible), langue.
7. **Langue** : rotation par canal, Français → Anglais → Arabe → Français… (d'après la colonne Langue du dernier contenu de ce canal dans Content). Jamais de darija.
8. Générer texte (hook, légende, hashtags) et visuels via l'**API Gemini de Google** (Imagen / Veo). Secours possible : gabarits Benidex + ffmpeg.
9. Ranger les fichiers dans le dépôt GitHub : `Prod/AAAA-MM-JJ/<produit>/` (fichiers directement dans le dossier du produit : `<output>-<canal>.mp4`, `<output>-<canal>-legende.txt`, `sources.txt`) ; commit + push sur la **branche principale** du dépôt, sans jamais créer de branche ; chemin dans Folder.
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

## Mise à jour (option A)
- Photos : colonne « Photos produit » → page du produit → recherche internet (jamais de photos de concurrents ni avec filigrane ; sources notées pour vérification des droits).
- Pas de génération d'images par IA ; texte, logo et bouton « Demandez votre devis » incrustés.
- Canaux vide → Échec « Aucun canal choisi ».

## Mise à jour (publication)
- Publication automatique via Windsor, au moment de l'exécution (pas de programmation) ; aucun réessai ; jamais de story, commentaire, publicité ou suppression.
- Vérifie à chaque exécution que le compte est connecté (`get_connectors`) et qu'une action adaptée existe (`list_actions`) ; sinon rien n'est publié.
- Statut Content : « Publié » seulement après un succès, avec l'identifiant média dans la page.
- Prérequis : connecteur Windsor et connecteur Notion attachés à la routine dans l'interface claude.ai.

## Mise à jour (une ligne par canal)
- Une ligne du Media Plan = un seul canal. Pour Instagram et TikTok : deux lignes.
- Statut final : « Traité » seulement si créé **et** publié ; sinon « Échec » avec la raison précise dans « Explication échec ».
- Heure d'exécution : 18 h GMT.
