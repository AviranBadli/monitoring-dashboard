"""Cost Timeseries model"""

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class CostTimeseries(Base):
    """Cost data from Apptio or other billing sources"""

    __tablename__ = "cost_timeseries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)

    node_name = Column(String, ForeignKey("gpu_nodes.name"), nullable=False, index=True)
    workload_type_name = Column(String, ForeignKey("workload_types.name"), nullable=False)

    # Relationships
    node = relationship("GPUNode", back_populates="cost_timeseries")
    workload_type = relationship("WorkloadType", back_populates="cost_timeseries")
