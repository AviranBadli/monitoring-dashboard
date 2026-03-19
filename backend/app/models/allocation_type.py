"""Allocation Type model"""

from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class AllocationType(Base):
    """Allocation Type (primary, secondary)"""

    __tablename__ = "allocation_types"

    name = Column(String, primary_key=True, index=True)
    priority = Column(Integer, nullable=False)  # 1 for primary, 2 for secondary, etc.

    # Relationships
    allocations = relationship("Allocation", back_populates="allocation_type")
