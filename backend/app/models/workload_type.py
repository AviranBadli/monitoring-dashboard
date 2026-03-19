"""Workload Type model"""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class WorkloadType(Base):
    """Workload Type (committed, on-demand, spot)"""

    __tablename__ = "workload_types"

    name = Column(String, primary_key=True, index=True)

    # Relationships
    allocations = relationship("Allocation", back_populates="workload_type")
    cost_timeseries = relationship("CostTimeseries", back_populates="workload_type")
