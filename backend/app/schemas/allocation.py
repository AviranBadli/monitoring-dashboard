"""Allocation schemas"""

from datetime import datetime
from pydantic import BaseModel


class AllocationBase(BaseModel):
    """Base Allocation schema"""

    gpu_uuid: str
    team_name: str
    workload_type_name: str
    allocation_type_name: str
    start_time: datetime
    end_time: datetime


class AllocationCreate(AllocationBase):
    """Schema for creating an allocation"""

    pass


class AllocationUpdate(BaseModel):
    """Schema for updating an allocation"""

    start_time: datetime | None = None
    end_time: datetime | None = None
    team_name: str | None = None


class Allocation(AllocationBase):
    """Schema for allocation response"""

    id: int

    model_config = {"from_attributes": True}


class AllocationQuery(BaseModel):
    """Schema for querying allocations"""

    team_name: str | None = None
    gpu_uuid: str | None = None
    cluster_name: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
