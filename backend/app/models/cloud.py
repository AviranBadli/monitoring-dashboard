"""Cloud provider model"""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Cloud(Base):
    """Cloud provider (AWS, GCP, Azure, IBM Cloud, OCI)"""

    __tablename__ = "clouds"

    name = Column(String, primary_key=True, index=True)

    # Relationships
    instance_types = relationship("InstanceType", back_populates="cloud")
    clusters = relationship("GPUCluster", back_populates="cloud")
