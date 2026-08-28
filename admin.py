import csv
import functools
import hmac
import io
import os

from flask import Blueprint, Response, flash, redirect, render_template, request, session, url_for

from emails import notify_customer, send_bulk
from extensions import db, limiter
from models import (
    QUOTE_STATUSES, ContactMessage, Division, QuoteRequest, ServiceItem,
    Subscriber, Testimonial,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me")


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapped


@admin_bp.context_processor
def inject_notification_counts():
    if not session.get("admin_logged_in"):
        return {}
    return {
        "nav_pending_quotes": QuoteRequest.query.filter_by(status="pending").count(),
        "nav_unread_messages": ContactMessage.query.filter_by(is_read=False).count(),
        "nav_pending_testimonials": Testimonial.query.filter_by(approved=False).count(),
    }


@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes", methods=["POST"])
def login():
    if request.method == "POST":
        if hmac.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD):
            session.clear()
            session["admin_logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin.dashboard"))
        flash("Mot de passe incorrect.", "error")
    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@login_required
def dashboard():
    stats = {
        "quotes": QuoteRequest.query.count(),
        "pending_quotes": QuoteRequest.query.filter_by(status="pending").count(),
        "messages": ContactMessage.query.count(),
        "unread_messages": ContactMessage.query.filter_by(is_read=False).count(),
        "testimonials_pending": Testimonial.query.filter_by(approved=False).count(),
        "subscribers": Subscriber.query.count(),
    }

    activity = []
    for q in QuoteRequest.query.order_by(QuoteRequest.created_at.desc()).limit(5).all():
        activity.append({"text": f"{q.name} a demandé un devis — {q.service_interest}",
                          "time": q.created_at, "url": url_for("admin.quotes")})
    for m in ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all():
        activity.append({"text": f"{m.name} a envoyé un message", "time": m.created_at,
                          "url": url_for("admin.messages")})
    for t in Testimonial.query.order_by(Testimonial.created_at.desc()).limit(5).all():
        activity.append({"text": f"{t.name} a laissé un témoignage", "time": t.created_at,
                          "url": url_for("admin.testimonials")})
    activity.sort(key=lambda item: item["time"], reverse=True)

    return render_template("admin/dashboard.html", stats=stats, activity=activity[:8])


# --- Quote requests ---------------------------------------------------

@admin_bp.route("/devis")
@login_required
def quotes():
    status_filter = request.args.get("status", "")
    search = request.args.get("q", "").strip()

    query = QuoteRequest.query
    if status_filter in QUOTE_STATUSES:
        query = query.filter_by(status=status_filter)
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(QuoteRequest.name.ilike(like), QuoteRequest.email.ilike(like),
                                     QuoteRequest.company.ilike(like)))

    all_quotes = query.order_by(QuoteRequest.created_at.desc()).all()
    return render_template("admin/quotes.html", quotes=all_quotes, statuses=QUOTE_STATUSES,
                            status_filter=status_filter, search=search)


@admin_bp.route("/devis/<int:quote_id>/status", methods=["POST"])
@login_required
def update_quote_status(quote_id):
    quote_request = QuoteRequest.query.get_or_404(quote_id)
    new_status = request.form.get("status")
    if new_status in QUOTE_STATUSES and new_status != quote_request.status:
        quote_request.status = new_status
        db.session.commit()

        status_labels = {
            "pending": "en attente", "contacted": "en cours de traitement",
            "won": "confirmée", "lost": "clôturée",
        }
        if new_status in ("contacted", "won"):
            notify_customer(
                quote_request.email, "Mise à jour de votre demande de devis",
                f"Bonjour {quote_request.name},\n\nVotre demande concernant « {quote_request.service_interest} » "
                f"est maintenant : {status_labels.get(new_status, new_status)}.\n\nNotre équipe reste à votre "
                "disposition pour toute question.",
            )
        flash(f"Devis marqué comme « {new_status} ».", "success")
    return redirect(url_for("admin.quotes"))


@admin_bp.route("/devis/export.csv")
@login_required
def export_quotes_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nom", "Entreprise", "Email", "Téléphone", "Service", "Message", "Statut", "Reçu"])
    for q in QuoteRequest.query.order_by(QuoteRequest.created_at.desc()).all():
        writer.writerow([q.name, q.company or "", q.email, q.phone or "", q.service_interest or "",
                          q.message or "", q.status, q.created_at.strftime("%Y-%m-%d %H:%M")])
    return Response(output.getvalue(), mimetype="text/csv",
                     headers={"Content-Disposition": "attachment; filename=devis.csv"})


# --- Contact messages ---------------------------------------------------

@admin_bp.route("/messages")
@login_required
def messages():
    unread_only = request.args.get("unread") == "1"
    query = ContactMessage.query
    if unread_only:
        query = query.filter_by(is_read=False)
    all_messages = query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin/messages.html", messages=all_messages, unread_only=unread_only)


@admin_bp.route("/messages/<int:message_id>/read", methods=["POST"])
@login_required
def mark_message_read(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.is_read = True
    db.session.commit()
    return redirect(url_for("admin.messages"))


# --- Testimonials -----------------------------------------------------

@admin_bp.route("/temoignages")
@login_required
def testimonials():
    pending_only = request.args.get("pending") == "1"
    query = Testimonial.query
    if pending_only:
        query = query.filter_by(approved=False)
    all_testimonials = query.order_by(Testimonial.created_at.desc()).all()
    return render_template("admin/testimonials.html", testimonials=all_testimonials, pending_only=pending_only)


@admin_bp.route("/temoignages/<int:testimonial_id>/approve", methods=["POST"])
@login_required
def approve_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    testimonial.approved = True
    db.session.commit()
    flash("Témoignage approuvé — visible publiquement.", "success")
    return redirect(url_for("admin.testimonials"))


@admin_bp.route("/temoignages/<int:testimonial_id>/delete", methods=["POST"])
@login_required
def delete_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    db.session.delete(testimonial)
    db.session.commit()
    flash("Témoignage supprimé.", "success")
    return redirect(url_for("admin.testimonials"))


# --- Divisions & services -----------------------------------------------

@admin_bp.route("/divisions")
@login_required
def divisions():
    all_divisions = Division.query.order_by(Division.sort_order).all()
    return render_template("admin/divisions.html", divisions=all_divisions)


@admin_bp.route("/divisions/<int:division_id>/toggle", methods=["POST"])
@login_required
def toggle_division(division_id):
    division = Division.query.get_or_404(division_id)
    division.active = not division.active
    db.session.commit()
    return redirect(url_for("admin.divisions"))


@admin_bp.route("/divisions/<int:division_id>", methods=["GET", "POST"])
@login_required
def division_detail(division_id):
    division = Division.query.get_or_404(division_id)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_division":
            division.name = request.form.get("name", division.name).strip()
            division.tagline = request.form.get("tagline", division.tagline).strip()
            division.description = request.form.get("description", division.description).strip()
            db.session.commit()
            flash("Division mise à jour.", "success")
        elif action == "add_service":
            name = request.form.get("name", "").strip()
            bullets = request.form.get("bullets", "").strip()
            if name:
                division.services.append(ServiceItem(
                    name=name, bullets=bullets, sort_order=len(division.services),
                ))
                db.session.commit()
                flash("Service ajouté.", "success")
        return redirect(url_for("admin.division_detail", division_id=division.id))

    return render_template("admin/division_detail.html", division=division)


@admin_bp.route("/services/<int:service_id>/toggle", methods=["POST"])
@login_required
def toggle_service(service_id):
    service = ServiceItem.query.get_or_404(service_id)
    service.active = not service.active
    db.session.commit()
    return redirect(url_for("admin.division_detail", division_id=service.division_id))


@admin_bp.route("/services/<int:service_id>/delete", methods=["POST"])
@login_required
def delete_service(service_id):
    service = ServiceItem.query.get_or_404(service_id)
    division_id = service.division_id
    db.session.delete(service)
    db.session.commit()
    flash("Service supprimé.", "success")
    return redirect(url_for("admin.division_detail", division_id=division_id))


# --- Newsletter ---------------------------------------------------------

@admin_bp.route("/newsletter", methods=["GET", "POST"])
@login_required
def newsletter():
    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()
        addresses = [s.email for s in Subscriber.query.all()]

        if not subject or not body:
            flash("Le sujet et le message sont obligatoires.", "error")
        elif not addresses:
            flash("Il n'y a pas encore d'abonnés.", "error")
        else:
            sent, failed = send_bulk(addresses, subject, body)
            flash(f"Newsletter envoyée à {sent} abonné(s), {failed} échec(s).", "success" if sent else "error")
        return redirect(url_for("admin.newsletter"))

    subscribers = Subscriber.query.order_by(Subscriber.subscribed_at.desc()).all()
    return render_template("admin/newsletter.html", subscribers=subscribers)


@admin_bp.route("/subscribers/export.csv")
@login_required
def export_subscribers_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Email", "Inscrit le"])
    for s in Subscriber.query.order_by(Subscriber.subscribed_at.desc()).all():
        writer.writerow([s.email, s.subscribed_at.strftime("%Y-%m-%d %H:%M")])
    return Response(output.getvalue(), mimetype="text/csv",
                     headers={"Content-Disposition": "attachment; filename=abonnes.csv"})
