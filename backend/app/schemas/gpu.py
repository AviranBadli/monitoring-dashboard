"""GPU schemas"""

from datetime import datetime
from pydantic import BaseModel


class GPUBase(BaseModel):
    """Base GPU schema"""

    uuid: str
    gpu_number: int
    gpu_cluster: str
    model_name: str


class GPU(GPUBase):
    """Schema for GPU response"""

    node_name: str | None = None
    gpu_type_name: str | None = None
    last_seen: datetime
    first_discovered: datetime

    model_config = {"from_attributes": True}


class GPUWithAllocation(GPU):
    """GPU with current allocation info"""

    current_allocation: dict | None = None
