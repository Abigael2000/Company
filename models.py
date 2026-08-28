from datetime import datetime

from extensions import db

QUOTE_STATUSES = ("pending", "contacted", "won", "lost")


class Division(db.Model):
    """One of the company's main business divisions (e.g. Ressources Humaines)."""
    __tablename__ = "divisions"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(8), default="🏢")  # single emoji used as a lightweight visual marker
    sort_order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    services = db.relationship(
        "ServiceItem", backref="division", lazy=True,
        order_by="ServiceItem.sort_order", cascade="all, delete-orphan",
    )


class ServiceItem(db.Model):
    """A specific service offered within a division (e.g. Recrutement & Placement)."""
    __tablename__ = "service_items"

    id = db.Column(db.Integer, primary_key=True)
    division_id = db.Column(db.Integer, db.ForeignKey("divisions.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    bullets = db.Column(db.Text)  # newline-separated list, rendered as a bullet list
    sort_order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True, nullable=False)

    def bullet_list(self):
        return [b.strip() for b in (self.bullets or "").split("\n") if b.strip()]


class QuoteRequest(db.Model):
    """A 'Demander un devis' submission — a lead asking about a specific service."""
    __tablename__ = "quote_requests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120))
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    service_interest = db.Column(db.String(120))  # free text: division/service name or "Autre"
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120))
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    service_interest = db.Column(db.String(120))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Testimonial(db.Model):
    """A client testimonial, submitted publicly, published once approved."""
    __tablename__ = "testimonials"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120))
    comment = db.Column(db.Text, nullable=False)
    approved = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Subscriber(db.Model):
    """Actualités / newsletter mailing list."""
    __tablename__ = "subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
