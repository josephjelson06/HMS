import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Kiosk(Base, TimestampMixin):
    __tablename__ = "kiosks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    device_id: Mapped[str | None] = mapped_column(String(80), unique=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    token_last4: Mapped[str | None] = mapped_column(String(4))
    last_seen_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
