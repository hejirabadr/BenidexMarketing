# Agent benidexMarketingManager – spécification (brouillon)

> Statut : **non construit**. Décisions de Badr + questions ouvertes. À relire avec `CLAUDE.md` et `brand/brand-context.md`.

## Rôle
Lire le plan média dans Notion, puis produire pour chaque ligne le contenu (texte + visuels) du produit à couvrir, au format demandé (Reel, Vidéo ou Photo). L'agent **ne publie jamais** : Badr valide et publie.

## Notion (workspace « Benidex Marketing »)
- Plan média : base **Media Plan** – https://app.notion.com/p/b41156e74308469787fc77990de8141c (data source `collection://2dae0263-bdac-4824-b5a5-8f15c6b6df1e`)
  - Colonnes : Name, Produit, Catégorie, Output (Reel / Vidéo / Photo), Canaux (Instagram / Facebook / LinkedIn / TikTok, un ou plusieurs), Date prévue, Statut (À faire / En cours / Traité / Échec), Explication échec, Notes.
- Résultats : base **Content** – https://app.notion.com/p/97200538e2184433aa727f95e986936d (data source `collection://b8a3e041-ce0a-4e73-9ba8-a919e8bb29ac`)
  - Formats : Carrousel, Reel, Photo, Vidéo. Statut « À valider » à la création. Colonne Folder = chemin des fichiers.

## Fonctionnement décidé
1. Déclenchement **automatique** à **5 h heure de Casablanca** (UTC+1 ; UTC+0 pendant le ramadan).
2. Lire le Media Plan **dans l'ordre de la liste Notion**.
3. **Date prévue vide → ne pas exécuter** la ligne (pas d'échec).
4. Ligne traitée : statut « En cours ».
5. **Chercher le produit sur internet** (à partir de la **photo du produit**) pour bien comprendre son fonctionnement ; vérifier aussi sur benidex.com.
6. Choix **faits par l'agent** : canal (parmi ceux de la ligne), angle/public, langue (français, **anglais ou arabe selon le cas**, jamais de darija), hashtags (selon contenu et cible).
7. Produire texte **et visuels** (génération via l'API Gemini de Google : Imagen / Veo).
8. Ranger les fichiers dans un **répertoire** ; écrire le chemin dans Folder.
9. Créer la ligne dans Content en « À valider » ; ligne du plan → « Traité ».
10. **Si problème : statut « Échec » + explication dans « Explication échec »**, sans poser de question.
11. Si un contenu existe déjà pour ce produit : à confirmer (réponse « oui » ambiguë : refaire ?).

## Formats
- Reel : « selon les normes » (proposé : 9:16, 1080×1920, 15–30 s) – à confirmer.
- Vidéo : **20 secondes maximum**.
- Photo : proposé 4:5, 1080×1350 – à confirmer.

## Génération des visuels
- **Décision du 2026-11-06 : zéro budget, pas d'API Gemini** (quota image à 0 sur l'offre gratuite ; Imagen/Veo non listés). Socle retenu = **option 1 : montage local à partir des vraies photos de benidex.com**.
- Source des photos : API WordPress de benidex.com (`/wp-json/wp/v2/product/<id>` puis `/wp-json/wp/v2/media/<featured_media>`), accessible depuis l'environnement. Le produit reste fidèle (jamais généré, déformé ni rogné).
- **Photo (4:5, 1080×1350)** : `tools/make_photo.py <id_produit> [sortie.png] [--titre "..."]` (Pillow). Gabarit : logo, bandeau `#2EAADC`, carte photo, bloc `#0E72B5`, titre, bouton `#F29400` « Demandez votre devis », benidex.com. Aucun prix. Prototype validé sur 2 produits.
- **Reel / Vidéo** : à construire avec ffmpeg (photos + zoom/transitions + texte, 9:16, 15–30 s pour le Reel, ≤ 20 s pour la Vidéo).
- À faire : variante arabe (texte droite-à-gauche, police arabe + mise en forme des lettres), variante anglaise, variantes de gabarit, utilisation de plusieurs photos par produit (galerie).
- Limite connue : certaines photos du site sont petites (agrandies, donc un peu floues). Une meilleure source serait un fichier fourni par Badr.
- Option payante écartée pour l'instant (FLUX, OpenAI, fal.ai/Replicate) : à reconsidérer seulement pour des scènes générées ou de la vidéo animée par IA.

## Questions encore ouvertes
- Colonne « Photo produit » (fichier) à ajouter au Media Plan ? Nombre de photos par produit ?
- Répertoire de sortie : `output/AAAA-MM-JJ/<produit>/` dans le dépôt, ou Drive/Dropbox ?
- Lignes à traiter à 5 h : date = aujourd'hui seulement, ou aussi les retards ?
- Règle de langue (proposé : FR par défaut, EN pour LinkedIn et universités, AR pour Instagram/Facebook/TikTok grand public).
- Doublons : refaire ou sauter ?
- Formats exacts Reel / Photo.
- Modèle de l'agent (proposé : Sonnet 5.5).
- Checklist « Terminé » finale (proposition : aucun prix ; « Demandez votre devis » ; pas de BenQ ni « au meilleur prix au Maroc » ; produit présent sur benidex.com ; logo et couleurs respectés ; Reel 15–30 s ; vidéo ≤ 20 s ; canaux présents ; statuts Notion à jour).
- Exemple de contenu « parfait » dans Content ?
