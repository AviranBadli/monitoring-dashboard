"""Team model"""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Team(Base):
    """Team (ML Platform, AI Research, Data Science, etc.)"""

    __tablename__ = "teams"

    name = Column(String, primary_key=True, index=True)
    account_id = Column(String, nullable=True)
    account_name = Column(String, nullable=True)
    cost_center = Column(String, nullable=True)

    # Relationships
    owners = relationship("Owner", back_populates="team")
    nodes = relationship("GPUNode", back_populates="team")
    allocations = relationship("Allocation", back_populates="team")
