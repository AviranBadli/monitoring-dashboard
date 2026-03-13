"""Cost data endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_db
from app.models import CostTimeseries

router = APIRouter()


@router.get("/node/{node_name}")
def get_node_costs(
    node_name: str,
    start: datetime | None = None,
    end: datetime | None = None,
    db: Session = Depends(get_db),
):
    """Get cost data for a specific node over a time range"""
    query = db.query(CostTimeseries).filter(CostTimeseries.node_name == node_name)

    if start:
        query = query.filter(CostTimeseries.date >= start)
    if end:
        query = query.filter(CostTimeseries.date <= end)

    return query.all()


@router.get("/team/{team_name}")
def get_team_costs(
    team_name: str,
    start: datetime | None = None,
    end: datetime | None = None,
    db: Session = Depends(get_db),
):
    """
    Get cost data for a team over a time range.

    This is a placeholder - real implementation needs to:
    1. Query allocations for the team
    2. Get cost data for those allocated GPUs/nodes
    3. Attribute costs based on allocation percentages
    """
    return {
        "message": "Team cost attribution not yet implemented",
        "team": team_name,
        "start": start,
        "end": end,
    }
