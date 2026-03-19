"""Allocation model"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Allocation(Base):
    """GPU Node Allocation to a team for a time period"""

    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, index=True)
    node_name = Column(String, ForeignKey("gpu_nodes.name"), nullable=False, index=True)
    team_name = Column(String, ForeignKey("teams.name"), nullable=False, index=True)
    workload_type_name = Column(String, ForeignKey("workload_types.name"), nullable=False)
    allocation_type_name = Column(String, ForeignKey("allocation_types.name"), nullable=False)

    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)

    # Relationships
    node = relationship("GPUNode", back_populates="allocations")
    team = relationship("Team", back_populates="allocations")
    workload_type = relationship("WorkloadType", back_populates="allocations")
    allocation_type = relationship("AllocationType", back_populates="allocations")
