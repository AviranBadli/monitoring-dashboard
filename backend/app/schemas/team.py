"""Team schemas"""

from pydantic import BaseModel


class TeamBase(BaseModel):
    """Base Team schema"""

    name: str
    account_id: str | None = None
    account_name: str | None = None
    cost_center: str | None = None


class TeamCreate(TeamBase):
    """Schema for creating a team"""

    pass


class Team(TeamBase):
    """Schema for team response"""

    model_config = {"from_attributes": True}
