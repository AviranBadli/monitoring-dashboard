"""GPU Cluster model"""

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class GPUCluster(Base):
    """GPU Cluster"""

    __tablename__ = "gpu_clusters"

    name = Column(String, primary_key=True, index=True)
    cloud_name = Column(String, ForeignKey("clouds.name"), nullable=False)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=True)

    # Relationships
    cloud = relationship("Cloud", back_populates="clusters")
    owner = relationship("Owner", back_populates="clusters")
    nodes = relationship("GPUNode", back_populates="cluster")
