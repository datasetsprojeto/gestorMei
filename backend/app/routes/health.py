from datetime import UTC, datetime

from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db

health_bp = Blueprint("health", __name__)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()

@health_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "API rodando com sucesso",
        "timestamp": _utc_now_iso(),
        "version": "1.0.0"
    }), 200


@health_bp.route("/health/live", methods=["GET"])
def liveness():
    return jsonify({
        "status": "alive",
        "timestamp": _utc_now_iso(),
        "service": "gestormei-api"
    }), 200


@health_bp.route("/health/ready", methods=["GET"])
def readiness():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({
            "status": "ready",
            "database": "ok",
            "timestamp": _utc_now_iso()
        }), 200
    except Exception as exc:
        return jsonify({
            "status": "not_ready",
            "database": "error",
            "message": str(exc),
            "timestamp": _utc_now_iso()
        }), 503