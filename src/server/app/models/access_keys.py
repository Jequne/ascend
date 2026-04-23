from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timezone

from ..database import Base


class KeyStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"


class AccessKeys(Base):
    __tablename__ = "access_keys"

    id = Column(Integer, primary_key=True, index=True)
    access_key = Column(String, nullable=False, index=True)

    max_activates = Column(Integer, nullable=False)
    current_connections_available = Column(Integer, nullable=False)

    created_at = Column(
        DateTime, 
        nullable=False, 
        default=datetime.now(timezone.utc)
        )
    expires_at = Column(DateTime, nullable=False)

    status = Column(Enum(KeyStatus), default=KeyStatus.ACTIVE, nullable=False)

