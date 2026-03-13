"""GPU Node model"""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class GPUNode(Base):
    """GPU Node (physical or virtual machine with GPUs)"""

    __tablename__ = "gpu_nodes"

    name = Column(String, primary_key=True, index=True)
    cluster_name = Column(String, ForeignKey("gpu_clusters.name"), nullable=False)
    instance_type_name = Column(String, ForeignKey("instance_types.name"), nullable=False)
    team_name = Column(String, ForeignKey("teams.name"), nullable=False)

    # Relationships
    cluster = relationship("GPUCluster", back_populates="nodes")
    instance_type = relationship("InstanceType", back_populates="nodes")
    team = relationship("Team", back_populates="nodes")
    gpus = relationship("GPU", back_populates="node")
    cost_timeseries = relationship("CostTimeseries", back_populates="node")
