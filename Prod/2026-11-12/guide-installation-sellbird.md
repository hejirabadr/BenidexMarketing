# Guide d'installation de Sellbird sur votre ordinateur (Benidex)

> Préparé le 12/11/2026 à partir du dépôt officiel https://github.com/ethanplusai/sellbird
> (dernier commit consulté : `25ec839`, 10/11/2026).
> Tout ce qui est marqué **[À CONFIRMER]** dépend d'une décision de Badr.

## 1. Ce que fait Sellbird

Sellbird est un outil open source (licence AGPL-3.0) de **prospection par email**. Il tourne sur votre ordinateur et :

1. trouve des organisations qui correspondent à votre client type (OpenStreetMap gratuit, ou source payante avec coût affiché avant chaque recherche) ;
2. lit leur site web pour repérer des signaux d'achat (sans appel au modèle, sans coût) ;
3. trouve le décideur (2 personnes maximum par organisation) ;
4. vérifie l'adresse email (vérifiée, risquée, supposée ou invalide ; seules les adresses délivrables reçoivent un email) ;
5. rédige une courte séquence d'emails personnalisés et l'envoie depuis votre boîte ;
6. lit les réponses, prépare un brouillon de réponse et respecte immédiatement les désinscriptions.

Il « réfléchit » via **Claude Code sur votre abonnement Claude Pro ou Max** : pas de clé API, pas de facturation au token.

**Par défaut, aucun email ne part sans votre validation** (onglet *Outbox* du tableau de bord). Conformément à `CLAUDE.md` (les messages à des clients restent soumis à votre accord), **ne pas activer l'autopilot**.

## 2. Ce qu'il vous faut avant de commencer

| Élément | Détail |
|---|---|
| Ordinateur | macOS, Windows ou Linux. Sous Windows, utiliser Claude (pas Codex). |
| Python | **3.11 ou plus récent**. Sur Mac, `python3` est souvent en 3.9 : installer `python@3.13` avec Homebrew. |
| Git | Pour télécharger le projet. |
| Claude Code | La CLI `claude`, connectée à votre abonnement Pro ou Max (`claude login`). |
| Boîte d'envoi | Idéalement **Google Workspace sur un domaine secondaire** dédié à la prospection, jamais le domaine principal `benidex.com`. Microsoft 365 et SMTP fonctionnent aussi. **[À CONFIRMER]** : quelle boîte et quel domaine ? |
| DNS du domaine | SPF, DKIM et DMARC configurés sur le domaine d'envoi. |
| Warmup | Une période de « chauffe » de la boîte avant les premiers envois (14 jours minimum dans la configuration par défaut). Sellbird recommande TrulyInbox (service payant, lien affilié de l'auteur) : facultatif, **à décider par vous**. |

## 3. Installation pas à pas

### Option A : laisser Claude Code vous guider (la plus simple)

Ouvrez un terminal et lancez :

```bash
git clone https://github.com/ethanplusai/sellbird.git
```

```bash
cd sellbird
```

```bash
claude
```

Puis écrivez à Claude : **« set up Sellbird for me »**. Le fichier `CLAUDE.md` du projet transforme Claude Code en assistant d'installation : il vérifie ce qui manque, l'installe, vous pose les questions et entraîne Sellbird sur votre activité. Donnez-lui le contenu de la section 4 ci-dessous quand il vous demande votre produit et vos cibles.

### Option B : à la main

**1. Télécharger et installer** (sur Mac, remplacez `python3.13` par la version installée ; sous Windows, utilisez `py -3.13` et `.venv\Scripts\activate`) :

```bash
git clone https://github.com/ethanplusai/sellbird.git
```

```bash
cd sellbird
```

```bash
python3.13 -m venv .venv && source .venv/bin/activate && pip install -e .
```

**2. Renseigner les identifiants** (chaque variable est expliquée dans le fichier) :

```bash
cp .env.example .env
```

Ouvrez `.env` et remplissez **une seule** option d'envoi :
- **Gmail / Google Workspace** : `GMAIL_CLIENT_ID` et `GMAIL_CLIENT_SECRET` (créés dans Google Cloud Console → API Gmail → identifiant OAuth de type « Application de bureau »), puis lancez `sellbird gmail auth`.
- **Microsoft 365** : voir `docs/microsoft365.md`, puis `sellbird microsoft auth`.
- **SMTP/IMAP** : `SMTP_*` et `IMAP_*`.

Ne mettez jamais le fichier `.env` dans un dépôt Git : il contient vos secrets.

**3. Apprendre votre activité à partir du site** (crée `sellbird.local.yaml`) :

```bash
sellbird train https://www.benidex.com
```

**4. Corriger le fichier `sellbird.local.yaml`** avec les réglages Benidex de la section 4. **Important** : le site benidex.com contient des formules interdites (« au meilleur prix au Maroc ») et des numéros à ne pas utiliser. Relisez ce que `train` a appris.

**5. Confirmer les signaux de prospection** :

```bash
sellbird signals --confirm free
```

**6. Vérifier que le domaine d'envoi est prêt** :

```bash
sellbird warmup
```

**7. Trouver des organisations** (source gratuite par défaut ; `--estimate` montre le coût avant une source payante) :

```bash
sellbird discover
```

**8. Ouvrir le tableau de bord et lancer la boucle** :

```bash
sellbird dashboard
```

```bash
sellbird run
```

Le tableau de bord s'ouvre sur `http://127.0.0.1:5555` (lien privé affiché dans le terminal). La boucle relance un cycle toutes les 15 minutes tant que l'ordinateur et le terminal restent ouverts.

**Si vous voulez seulement la liste de prospects** (sans envoi), arrêtez-vous après l'étape 7 :

```bash
sellbird export
```

## 4. Réglages Benidex à mettre dans `sellbird.local.yaml`

Modèle à adapter. Les valeurs viennent de `brand/brand-context.md`. Les lignes **[À CONFIRMER]** sont à décider par vous.

```yaml
persona:
  name: "Badr HEJIRA"                 # [À CONFIRMER] qui signe les emails
  company: "Benidex"
  role: "CEO"                         # [À CONFIRMER]
  email: ""                           # [À CONFIRMER] adresse sur le domaine d'envoi
  tone: "professionnel, rassurant, orienté solutions, vouvoiement, phrases courtes, sans exagération"

product:
  name: "Benidex"
  description: "Fournisseur marocain de mobilier scolaire et de bureau, jouets éducatifs, écrans interactifs et solutions technologiques (infrastructure IT, audiovisuel, sécurité). Vente sur devis avec conseils d'experts."
  pricing: "Sur devis uniquement. Ne jamais citer de prix."
  key_benefits:
    - "Étendue de la gamme"
    - "Disponibilité du stock"
    - "Qualité, meilleur rapport qualité-prix"
  offer:
    primary: "Devis personnalisé avec conseils d'experts"
    goal: "get_reply"                 # [À CONFIRMER] get_reply ou book_call
    booking_url: ""

icp:
  industries:
    - "Écoles privées"
    - "Universités"
    - "Crèches"                       # [À CONFIRMER]
  titles:
    - "Directeur"
    - "Directrice"
    - "Fondateur"
    - "Responsable des achats"        # [À CONFIRMER]
  geography:
    - "Maroc"                         # [À CONFIRMER] villes ciblées

channels:
  email:
    provider: "gmail"                 # [À CONFIRMER] gmail | microsoft | smtp
    max_daily_sends: 20               # [À CONFIRMER] commencer bas
    require_approval: true            # À GARDER : rien ne part sans votre validation
    send_to_risky: false
    link_domains: ["benidex.com"]
    warmup:
      start_date: ""                  # [À CONFIRMER] date de début du warmup (AAAA-MM-JJ)
      min_days: 14
    signature:
      logo: ""                        # facultatif : PNG de 100 Ko maximum (le logo actuel fait 600 × 233 px)
      alt: "Benidex"
      link: "https://www.benidex.com"

usage:
  max_daily_claude_percent: 50        # garder de la marge pour votre propre usage de Claude
  quiet_hours:
    start: "20:00"
    end: "08:00"
    timezone: "Africa/Casablanca"

compliance:
  postal_address: "Résidence Chaimaa B RDC, Rue Bachir Ibrahimi, Casablanca"
  opt_out_line: "Pas intéressé ? Répondez-moi simplement et je ne vous écrirai plus."
  do_not_contact:
    # [À CONFIRMER] domaines web exacts des concurrents Eduhermex, Edumaster, Scody
    # + domaines de vos clients existants
```

**Règles de rédaction** : créez un fichier `skills/email_rules.md` (activé par `writer: email_rules: "skills/email_rules.md"`) avec les règles de marque :
- jamais de prix, appel à l'action « Demandez votre devis » ;
- ne jamais mentionner BenQ ni les noms de fournisseurs ;
- « meilleur rapport qualité-prix », jamais « au meilleur prix au Maroc » ;
- ne pas promettre installation, personnalisation ou garantie (non définies) ;
- livraison possible, avec des frais à la charge du client ;
- français par défaut, arabe ou anglais selon le public, **jamais de darija**.

## 5. Points d'attention

1. **Validation manuelle** : gardez `require_approval: true`. Relisez chaque email dans l'*Outbox*. Arrêt d'urgence : `sellbird sending pause`.
2. **Aspect légal (Maroc)** : la collecte de données personnelles et la prospection par email relèvent de la loi 09-08 et de la CNDP. Le service de vérification « Precleared » intégré à Sellbird **ne couvre pas le Maroc** (pays listés : GB, US, CA, DE, FR, AU, IE, NL, ES, IT, LV, AE, EG, QA). **Vérifiez vos obligations avec un conseiller avant les premiers envois.**
3. **Désinscription** : Sellbird reconnaît automatiquement les refus en français, anglais, espagnol et hébreu. En arabe, c'est le modèle qui les détecte (pas de règle automatique).
4. **Signature en arabe** : pour un email en arabe, mettez `signature: direction: "rtl"`.
5. **Ordinateur allumé** : Sellbird ne tourne que quand votre ordinateur et `sellbird run` sont actifs. Sur Mac et Windows, `sellbird autostart install` peut le lancer à l'ouverture de session.
6. **Crédits Claude** : Sellbird utilise votre abonnement Claude. `usage.max_daily_claude_percent` limite sa part ; `sellbird usage` affiche la consommation.

## 6. Commandes utiles

| Commande | Rôle |
|---|---|
| `sellbird status` | Résumé du pipeline |
| `sellbird outbox` | Emails en attente de validation |
| `sellbird sending pause` / `resume` | Arrêter / reprendre tous les envois |
| `sellbird suppressions add <adresse ou domaine>` | Ne jamais contacter |
| `sellbird export` | Prospects délivrables en CSV |
| `sellbird companies` | Toutes les organisations trouvées, et pourquoi elles n'ont pas été contactées |
| `sellbird usage` | Consommation de l'abonnement Claude |

Documentation complète (en anglais) : dossier `docs/` du projet, en particulier `docs/configuration.md`, `docs/approval-and-sending.md` et `docs/deliverability.md`.
