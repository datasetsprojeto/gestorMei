from flask import Blueprint, jsonify
import datetime
from sqlalchemy import text

from app.extensions import db

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "API rodando com sucesso",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }), 200


@health_bp.route("/health/live", methods=["GET"])
def liveness():
    return jsonify({
        "status": "alive",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "service": "gestormei-api"
    }), 200


@health_bp.route("/health/ready", methods=["GET"])
def readiness():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({
            "status": "ready",
            "database": "ok",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }), 200
    except Exception as exc:
        return jsonify({
            "status": "not_ready",
            "database": "error",
            "message": str(exc),
            "timestamp": datetime.datetime.utcnow().isoformat()
        }), 503