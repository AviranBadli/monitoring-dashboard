"""Cloud schemas"""

from pydantic import BaseModel


class CloudBase(BaseModel):
    """Base Cloud schema"""

    name: str


class CloudCreate(CloudBase):
    """Schema for creating a cloud"""

    pass


class Cloud(CloudBase):
    """Schema for cloud response"""

    model_config = {"from_attributes": True}
