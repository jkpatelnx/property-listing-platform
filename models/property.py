import uuid
from sqlalchemy import Column, String, DateTime, Text, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.base import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    city = Column(String(100), nullable=False, index=True)
    address = Column(String(500), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    bedrooms = Column(Integer, nullable=False, default=1)
    bathrooms = Column(Integer, nullable=False, default=1)
    property_type = Column(String(50), nullable=False, default="apartment")
    image_filename = Column(String(255), nullable=True)   # hero thumbnail (first uploaded image)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="properties")
    images = relationship(
        "PropertyImage",
        back_populates="property",
        cascade="all, delete-orphan",
        order_by="PropertyImage.display_order",
    )
    contact_requests = relationship("ContactRequest", back_populates="property", cascade="all, delete-orphan")

    @property
    def primary_image(self):
        """Return filename of first gallery image or fallback to image_filename."""
        if self.images:
            return self.images[0].filename
        return self.image_filename

    def __repr__(self):
        return f"<Property id={self.id} title={self.title}>"
