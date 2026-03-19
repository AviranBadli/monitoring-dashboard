"""Owner model"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Owner(Base):
    """Owner (person responsible for clusters/resources)"""

    __tablename__ = "owners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    team_name = Column(String, ForeignKey("teams.name"), nullable=True)

    # Relationships
    team = relationship("Team", back_populates="owners")
    clusters = relationship("GPUCluster", back_populates="owner")
