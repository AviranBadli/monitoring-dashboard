"""Instance Type model"""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class InstanceType(Base):
    """Instance Type from cloud provider (e.g., p4d.24xlarge, Standard_NV36ads_A10_v5)"""

    __tablename__ = "instance_types"

    name = Column(String, primary_key=True, index=True)
    cloud_name = Column(String, ForeignKey("clouds.name"), nullable=False)

    # Relationships
    cloud = relationship("Cloud", back_populates="instance_types")
    nodes = relationship("GPUNode", back_populates="instance_type")
    cost_timeseries = relationship("CostTimeseries", back_populates="instance_type")
