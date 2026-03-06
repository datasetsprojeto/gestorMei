from datetime import UTC, datetime
from app.extensions import db


def utc_now():
    return datetime.now(UTC)


class MonthlySnapshot(db.Model):
    __tablename__ = "monthly_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    total_sales = db.Column(db.Integer, nullable=False, default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    gross_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    saved_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    __table_args__ = (
        db.UniqueConstraint("user_id", "year", "month", name="uq_monthly_snapshot_user_period"),
        db.Index("idx_monthly_snapshot_period", "year", "month"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "year": self.year,
            "month": self.month,
            "total_sales": self.total_sales,
            "total_amount": float(self.total_amount),
            "gross_amount": float(self.gross_amount),
            "saved_at": self.saved_at.isoformat() if self.saved_at else None,
        }
