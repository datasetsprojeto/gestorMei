from datetime import datetime
import json

from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    resource_type = db.Column(db.String(80), nullable=False, index=True)
    resource_id = db.Column(db.String(120), nullable=True)
    details_json = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    def set_details(self, details):
        if details is None:
            self.details_json = None
            return
        self.details_json = json.dumps(details, ensure_ascii=False)

    def get_details(self):
        if not self.details_json:
            return None
        try:
            return json.loads(self.details_json)
        except Exception:
            return {"raw": self.details_json}

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "actor_user_id": self.actor_user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.get_details(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
