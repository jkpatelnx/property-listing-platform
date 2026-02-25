import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(10), nullable=False, default="user")  # "admin" | "user"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    properties = relationship("Property", back_populates="owner", cascade="all, delete-orphan")
    contact_requests = relationship("ContactRequest", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"
