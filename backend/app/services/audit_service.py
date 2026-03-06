from flask import request

from app.extensions import db
from app.models.audit_log import AuditLog


def log_audit(owner_id, actor_user_id, action, resource_type, resource_id=None, details=None):
    try:
        entry = AuditLog(
            owner_id=owner_id,
            actor_user_id=actor_user_id,
            action=str(action),
            resource_type=str(resource_type),
            resource_id=str(resource_id) if resource_id is not None else None,
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
            user_agent=(request.user_agent.string if request.user_agent else None),
        )
        entry.set_details(details)
        db.session.add(entry)
    except Exception:
        # Auditoria não deve quebrar fluxo principal.
        pass
