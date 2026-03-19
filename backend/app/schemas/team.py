"""Team schemas"""

from pydantic import BaseModel


class TeamBase(BaseModel):
    """Base Team schema"""

    name: str


class TeamCreate(TeamBase):
    """Schema for creating a team"""

    pass


class Team(TeamBase):
    """Schema for team response"""

    model_config = {"from_attributes": True}
