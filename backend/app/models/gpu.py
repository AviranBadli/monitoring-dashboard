"""GPU model"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class GPU(Base):
    """Individual GPU discovered from DCGM metrics"""

    __tablename__ = "gpus"

    uuid = Column(String, primary_key=True, index=True)
    gpu_number = Column(Integer, nullable=False)  # GPU number within the node
    gpu_cluster = Column(String, nullable=False, index=True)  # From Prometheus labels
    model_name = Column(String, nullable=False)  # e.g., "NVIDIA A100-SXM4-80GB"
    node_name = Column(String, ForeignKey("gpu_nodes.name"), nullable=True)
    gpu_type_name = Column(String, ForeignKey("gpu_types.name"), nullable=True)

    # Metadata
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    first_discovered = Column(DateTime, default=datetime.utcnow)

    # Relationships
    node = relationship("GPUNode", back_populates="gpus")
    gpu_type = relationship("GpuType", back_populates="gpus")
    allocations = relationship("Allocation", back_populates="gpu")
