import os
import re
import time
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, Response, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect

from admin import admin_bp
from emails import notify_company, notify_customer
from extensions import db, limiter
from models import ContactMessage, Division, QuoteRequest, ServiceItem, Subscriber, Testimonial
from utils import is_spam

load_dotenv()

DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "")  # e.g. "243900000000", no + or spaces

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# Render (and most PaaS providers) hand out DATABASE_URL as "postgres://",
# but SQLAlchemy 1.4+ requires "postgresql://" — normalize so the same code
# works locally (SQLite) and on Render (Postgres) unchanged.
_db_url = os.environ.get("DATABASE_URL", "sqlite:///site.db")
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = _db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- Security hardening ---------------------------------------------------
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = not DEBUG
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

db.init_app(app)
limiter.init_app(app)
app.register_blueprint(admin_bp)
CSRFProtect(app)


@app.context_processor
def inject_globals():
    nav_divisions = Division.query.filter_by(active=True).order_by(Division.sort_order).all()
    return {"whatsapp_number": WHATSAPP_NUMBER, "nav_divisions": nav_divisions}


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


@app.errorhandler(429)
def rate_limited(_error):
    return render_template("429.html"), 429


@app.errorhandler(500)
def server_error(_error):
    return render_template("500.html"), 500


# ---------------------------------------------------------------------------
# Seed data — the 5 business divisions and their services, from the brief.
# Runs once: if divisions already exist, this is a no-op.
# ---------------------------------------------------------------------------

def seed_divisions_if_empty():
    if Division.query.count() > 0:
        return

    data = [
        dict(
            slug="tourisme-commerce", icon="✈️", name="Tourisme & Commerce",
            tagline="Solutions touristiques et opérations d'import-export",
            description="Des services touristiques adaptés aux particuliers, entreprises et organisations, "
                         "combinés à des solutions d'importation, d'exportation et d'approvisionnement pour "
                         "faciliter vos opérations commerciales.",
            services=[
                dict(name="Tourisme & Voyages",
                     bullets="Organisation de services touristiques\nMise à disposition de produits touristiques\n"
                             "Solutions pour les déplacements\nOrganisation de séjours\nPackages touristiques"),
                dict(name="Import-Export",
                     bullets="Importation de biens mobiliers et produits alimentaires\nExportation\n"
                             "Approvisionnement\nCommerce"),
            ],
        ),
        dict(
            slug="ressources-humaines", icon="🤝", name="Ressources Humaines",
            tagline="Recrutement, formation et gestion du personnel",
            description="Nous accompagnons les entreprises dans la gestion, le développement et la mise à "
                         "disposition de leurs ressources humaines, du recrutement à la paie.",
            services=[
                dict(name="Recrutement & Placement",
                     bullets="Identification des profils\nSélection des candidats\nPlacement du personnel\n"
                             "Gestion des besoins en recrutement"),
                dict(name="Formation professionnelle",
                     bullets="Formation professionnelle\nRenforcement des capacités\n"
                             "Développement des compétences\nProgrammes adaptés aux entreprises"),
                dict(name="Externalisation RH & Payroll",
                     bullets="Gestion de la paie\nAdministration du personnel\nExternalisation RH\n"
                             "Déclarations fiscales"),
                dict(name="Sous-traitance de personnel",
                     bullets="Mise à disposition de personnel conformément à la législation du travail "
                             "en République Démocratique du Congo"),
                dict(name="Enquêtes & Vérification",
                     bullets="Enquêtes de moralité\nVérification des références\n"
                             "Vérification des antécédents professionnels"),
            ],
        ),
        dict(
            slug="logistique-services-entreprises", icon="🚚", name="Logistique & Services aux entreprises",
            tagline="Logistique, transport, catering et accompagnement aux appels d'offres",
            description="Des solutions logistiques fiables pour faciliter vos opérations, assurer le transport "
                         "de vos biens et collaborateurs, et vous accompagner dans l'analyse des appels d'offres.",
            services=[
                dict(name="Logistique", bullets="Coordination et organisation des opérations logistiques"),
                dict(name="Catering",
                     bullets="Solutions de restauration adaptées aux besoins professionnels et événementiels"),
                dict(name="Transport terrestre", bullets="Transport de personnes et de biens"),
                dict(name="Appels d'offres",
                     bullets="Analyse des dossiers\nIdentification des exigences\nAnalyse des critères\n"
                             "Vérification documentaire\nAssistance à la préparation"),
            ],
        ),
        dict(
            slug="solutions-techniques", icon="🛠️", name="Solutions techniques",
            tagline="Études, installation, expertise et maintenance",
            description="Des services techniques couvrant les études, le montage, l'installation, l'expertise "
                         "et la maintenance, y compris en informatique industrielle.",
            services=[
                dict(name="Études", bullets="Travaux d'étude et analyse technique des projets"),
                dict(name="Montage", bullets="Travaux de montage et mise en œuvre"),
                dict(name="Installation", bullets="Installation de systèmes et équipements"),
                dict(name="Expertise", bullets="Services d'expertise et d'évaluation technique"),
                dict(name="Maintenance", bullets="Maintenance et accompagnement technique"),
                dict(name="Informatique industrielle",
                     bullets="Solutions et services techniques dans le domaine de l'informatique industrielle"),
            ],
        ),
        dict(
            slug="communication-fournitures", icon="🖨️", name="Communication & Fournitures",
            tagline="Impression, design graphique, équipements de sécurité et fournitures de bureau",
            description="Donnez une identité professionnelle à votre entreprise grâce à nos solutions de "
                         "conception graphique, d'impression, et à nos fournitures et équipements de sécurité.",
            services=[
                dict(name="Conception graphique",
                     bullets="Logos\nIdentité visuelle\nAffiches\nFlyers\nBrochures\nSupports publicitaires"),
                dict(name="Impression",
                     bullets="Documents professionnels\nCartes de visite\nBrochures\nAffiches\n"
                             "Supports promotionnels"),
                dict(name="Équipements de sécurité",
                     bullets="Équipements de protection\nMatériel de sécurité\nÉquipements professionnels"),
                dict(name="Fournitures de bureau",
                     bullets="Papeterie\nFournitures administratives\nMatériel de bureau"),
            ],
        ),
    ]

    for order, div in enumerate(data):
        division = Division(
            slug=div["slug"], name=div["name"], tagline=div["tagline"],
            description=div["description"], icon=div["icon"], sort_order=order,
        )
        for s_order, svc in enumerate(div["services"]):
            division.services.append(ServiceItem(
                name=svc["name"], bullets=svc["bullets"], sort_order=s_order,
            ))
        db.session.add(division)

    db.session.commit()


with app.app_context():
    db.create_all()
    seed_divisions_if_empty()


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    divisions = Division.query.filter_by(active=True).order_by(Division.sort_order).all()
    testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.created_at.desc()).limit(3).all()
    return render_template("index.html", divisions=divisions, testimonials=testimonials)


@app.route("/a-propos")
def about():
    return render_template("about.html")


@app.route("/services")
def services():
    divisions = Division.query.filter_by(active=True).order_by(Division.sort_order).all()
    return render_template("services.html", divisions=divisions)


@app.route("/services/<slug>")
def division_detail(slug):
    division = Division.query.filter_by(slug=slug, active=True).first_or_404()
    other_divisions = Division.query.filter(Division.slug != slug, Division.active == True).order_by(Division.sort_order).all()  # noqa: E712
    return render_template("division.html", division=division, other_divisions=other_divisions)


@app.route("/secteurs")
def sectors():
    return render_template("sectors.html")


@app.route("/realisations")
def projects():
    return render_template("projects.html")


@app.route("/temoignages", methods=["GET", "POST"])
@limiter.limit("8 per hour", methods=["POST"])
def testimonials():
    if request.method == "POST":
        if is_spam(request.form):
            flash("Une erreur est survenue. Merci de réessayer.", "error")
            return redirect(url_for("testimonials"))

        name = request.form.get("name", "").strip()
        company = request.form.get("company", "").strip()
        comment = request.form.get("comment", "").strip()

        if not name or not comment:
            flash("Merci de renseigner votre nom et votre commentaire.", "error")
            return redirect(url_for("testimonials"))

        db.session.add(Testimonial(name=name, company=company, comment=comment))
        db.session.commit()
        notify_company("Nouveau témoignage soumis",
                        f"{name}{f' ({company})' if company else ''} a laissé un témoignage:\n\n{comment}\n\n"
                        "Approuvez-le depuis le panneau d'administration.")
        flash("Merci pour votre témoignage ! Il sera publié après validation.", "success")
        return redirect(url_for("testimonials"))

    approved = Testimonial.query.filter_by(approved=True).order_by(Testimonial.created_at.desc()).all()
    return render_template("testimonials.html", testimonials=approved, now=time.time())


@app.route("/contact", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def contact():
    divisions = Division.query.filter_by(active=True).order_by(Division.sort_order).all()

    if request.method == "POST":
        if is_spam(request.form):
            flash("Une erreur est survenue. Merci de réessayer.", "error")
            return redirect(url_for("contact"))

        name = request.form.get("name", "").strip()
        company = request.form.get("company", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        service_interest = request.form.get("service_interest", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Merci de renseigner votre nom, votre email et votre message.", "error")
            return redirect(url_for("contact"))
        if not EMAIL_RE.match(email):
            flash("Merci de renseigner une adresse email valide.", "error")
            return redirect(url_for("contact"))

        db.session.add(ContactMessage(
            name=name, company=company, email=email, phone=phone,
            service_interest=service_interest, message=message,
        ))
        db.session.commit()

        notify_company(
            f"Nouveau message de contact — {name}",
            f"Nom: {name}\nEntreprise: {company or 'Non renseignée'}\nEmail: {email}\n"
            f"Téléphone: {phone or 'Non renseigné'}\nService recherché: {service_interest or 'Non précisé'}\n\n"
            f"Message:\n{message}",
            reply_to=email,
        )
        notify_customer(
            email, "Nous avons bien reçu votre message",
            f"Bonjour {name},\n\nMerci de nous avoir contactés. Nous avons bien reçu votre message et "
            f"reviendrons vers vous dans les meilleurs délais.\n\nVotre message :\n{message}",
        )

        flash("Votre message a été envoyé. Nous vous répondrons rapidement !", "success")
        return redirect(url_for("contact"))

    preselected = request.args.get("service", "")
    return render_template("contact.html", divisions=divisions, preselected=preselected, now=time.time())


@app.route("/devis", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def quote():
    divisions = Division.query.filter_by(active=True).order_by(Division.sort_order).all()

    if request.method == "POST":
        if is_spam(request.form):
            flash("Une erreur est survenue. Merci de réessayer.", "error")
            return redirect(url_for("quote"))

        name = request.form.get("name", "").strip()
        company = request.form.get("company", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        service_interest = request.form.get("service_interest", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not service_interest:
            flash("Merci de renseigner votre nom, votre email et le service recherché.", "error")
            return redirect(url_for("quote"))
        if not EMAIL_RE.match(email):
            flash("Merci de renseigner une adresse email valide.", "error")
            return redirect(url_for("quote"))

        db.session.add(QuoteRequest(
            name=name, company=company, email=email, phone=phone,
            service_interest=service_interest, message=message,
        ))
        db.session.commit()

        notify_company(
            f"Nouvelle demande de devis — {service_interest}",
            f"Nom: {name}\nEntreprise: {company or 'Non renseignée'}\nEmail: {email}\n"
            f"Téléphone: {phone or 'Non renseigné'}\nService: {service_interest}\n\n"
            f"Message:\n{message or 'Aucun'}",
            reply_to=email,
        )
        notify_customer(
            email, "Votre demande de devis a bien été reçue",
            f"Bonjour {name},\n\nMerci pour votre demande concernant : {service_interest}.\n"
            "Notre équipe l'étudie et reviendra vers vous rapidement avec une proposition adaptée.\n\n"
            f"Détails transmis :\n{message or 'Aucun message complémentaire'}",
        )

        flash("Votre demande de devis a été envoyée ! Nous revenons vers vous rapidement.", "success")
        return redirect(url_for("quote"))

    preselected = request.args.get("service", "")
    return render_template("quote.html", divisions=divisions, preselected=preselected, now=time.time())


@app.route("/subscribe", methods=["POST"])
@limiter.limit("5 per hour")
def subscribe():
    if is_spam(request.form):
        flash("Une erreur est survenue. Merci de réessayer.", "error")
        return redirect(request.referrer or url_for("home"))

    email = request.form.get("newsletter_email", "").strip()
    if not email or not EMAIL_RE.match(email):
        flash("Merci de renseigner une adresse email valide.", "error")
        return redirect(request.referrer or url_for("home"))

    if Subscriber.query.filter_by(email=email).first():
        flash("Vous êtes déjà inscrit(e) !", "success")
    else:
        db.session.add(Subscriber(email=email))
        db.session.commit()
        notify_company("Nouvel abonné aux actualités", f"{email} vient de s'inscrire à la newsletter.")
        flash("Inscription confirmée, merci !", "success")

    return redirect(request.referrer or url_for("home"))


@app.route("/robots.txt")
def robots_txt():
    lines = ["User-agent: *", "Allow: /", f"Sitemap: {request.url_root}sitemap.xml"]
    return Response("\n".join(lines), mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    pages = [
        url_for("home", _external=True), url_for("about", _external=True),
        url_for("services", _external=True), url_for("sectors", _external=True),
        url_for("projects", _external=True), url_for("testimonials", _external=True),
        url_for("contact", _external=True), url_for("quote", _external=True),
    ]
    for division in Division.query.filter_by(active=True).all():
        pages.append(url_for("division_detail", slug=division.slug, _external=True))

    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    body += [f"<url><loc>{page}</loc></url>" for page in pages]
    body.append("</urlset>")
    return Response("\n".join(body), mimetype="application/xml")


if __name__ == "__main__":
    app.run(debug=DEBUG)
