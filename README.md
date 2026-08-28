# JADAS-SAS — Site institutionnel (Flask)

Site multi-pages pour JADAS-SAS, structuré autour de 5 divisions d'activité,
avec base de données, panneau d'administration, et formulaires de contact
et de demande de devis envoyés par email.

## Structure du site

- **Accueil** — présentation, domaines d'expertise, pourquoi nous choisir,
  notre approche, témoignages, appel à l'action
- **À propos** — mission, vision, valeurs (l'historique de l'entreprise
  reste à compléter — voir `templates/about.html`)
- **Nos services** — vue d'ensemble des 5 divisions :
  1. Tourisme & Commerce
  2. Ressources Humaines
  3. Logistique & Services aux entreprises
  4. Solutions techniques
  5. Communication & Fournitures
- **Pages de division** (`/services/<slug>`) — détail des services de
  chaque division, générées dynamiquement depuis la base de données
- **Nos secteurs** — les types d'organisations desservies
- **Réalisations** — page prête à accueillir vos projets une fois disponibles
- **Témoignages** — affichage + formulaire de soumission (modéré)
- **Contact** — formulaire avec sélection du service recherché
- **Demander un devis** — formulaire dédié, préremplissable depuis les
  pages de division (`?service=NomDuService`)
- **Panneau d'administration** (`/admin`) — gestion des devis, messages,
  témoignages, divisions/services, et newsletter

## 1. Installation

```bash
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configuration

```bash
cp .env.example .env
```

Renseignez dans `.env` :
- `SECRET_KEY` — chaîne aléatoire
- `ADMIN_PASSWORD` — mot de passe du panneau `/admin`
- `SMTP_*` / `COMPANY_EMAIL` — voir section email ci-dessous
- `WHATSAPP_NUMBER` — numéro WhatsApp au format international, chiffres
  uniquement (ex : `243900000000`). Laissez vide pour masquer le bouton
  flottant tant que le numéro n'est pas disponible.

### Email (exemple avec Gmail)
1. Activer la validation en 2 étapes sur le compte Google.
2. Compte Google → Sécurité → Mots de passe des applications → créer un
   mot de passe pour "Mail".
3. Utiliser ce mot de passe de 16 caractères comme `SMTP_PASSWORD`.

## 3. Lancer le site

```bash
python app.py
```

- Site : `http://127.0.0.1:5000`
- Admin : `http://127.0.0.1:5000/admin`

Au premier lancement, la base de données est créée automatiquement et les
5 divisions ainsi que leurs services sont préremplis à partir du contenu
transmis pour le projet.

## Contenu à compléter avant la mise en ligne définitive

Ces éléments sont volontairement laissés en placeholder pour ne pas
inventer d'informations sur l'entreprise :

- **Logo** — actuellement un logo texte simple dans `templates/base.html`
  et `static/favicon.svg`
- **Coordonnées** — téléphone, email et adresse (visibles sur la page
  Contact et dans le footer, marqués « à compléter »)
- **Historique de l'entreprise** — section « Qui sommes-nous » de la page
  À propos (`templates/about.html`)
- **Réalisations / projets** — la page `/realisations` est prête à
  recevoir du contenu une fois les premiers projets disponibles

## Architecture technique

```
app.py          Routes publiques + données de départ (5 divisions/services)
admin.py        Blueprint admin : connexion + toutes les routes /admin/*
models.py       Tables : Division, ServiceItem, QuoteRequest, ContactMessage,
                Testimonial, Subscriber
emails.py       Envoi SMTP (email unique + newsletter en masse)
extensions.py   Instances partagées : SQLAlchemy `db`, Flask-Limiter `limiter`
utils.py        Anti-spam (honeypot + délai minimum de soumission)
templates/      Pages publiques
templates/admin/  Pages d'administration
static/style.css Palette bleu marine / ambre, animations au défilement
static/main.js  Menu mobile, animations, compteurs animés, préremplissage
```

## Sécurité

- Protection CSRF sur tous les formulaires (Flask-WTF)
- Limitation de débit (Flask-Limiter) : 5 tentatives de connexion admin
  par 15 min, 8–10 soumissions/heure sur les formulaires publics
- Comparaison du mot de passe admin en temps constant (`hmac.compare_digest`)
- Cookies de session sécurisés, expiration après 2h d'inactivité
- En-têtes de sécurité (anti-clickjacking, anti-MIME-sniffing, HSTS en prod)
- Pages d'erreur personnalisées (404, 429, 500)
- Anti-spam (honeypot + délai minimum) sur tous les formulaires publics

## Notifications admin

Le panneau `/admin` affiche des badges avec compteurs en temps réel pour
les devis en attente, messages non lus et témoignages à valider. Un email
est envoyé à `COMPANY_EMAIL` pour chaque nouveau devis, message, témoignage
et abonnement newsletter.

## Mise en ligne (Render + Cloudflare)

1. Poussez le projet sur GitHub.
2. Sur Render : New → Blueprint, connectez le dépôt — `render.yaml` crée
   automatiquement le service web et une base Postgres gratuite.
3. Renseignez les variables marquées `sync: false` (ADMIN_PASSWORD,
   SMTP_*, COMPANY_EMAIL, WHATSAPP_NUMBER).
4. Une fois déployé, ajoutez votre domaine Cloudflare dans Render →
   Settings → Custom Domain, puis créez l'enregistrement CNAME indiqué
   dans Cloudflare (en mode « DNS only » le temps que Render émette son
   certificat SSL, avant de réactiver le proxy Cloudflare si souhaité).
5. Une fois le domaine actif, mettez à jour le logo, les coordonnées, et
   soumettez `/sitemap.xml` à Google Search Console.

La base Postgres gratuite de Render expire après 90 jours sans mise à
niveau — pensez à surveiller cette échéance.
